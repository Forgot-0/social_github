import asyncio
import contextlib
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import orjson
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.chats.config import chat_config
from app.chats.dtos.websocket import WSConnection
from app.chats.services.delivery_router import (
    active_subscription_key,
    active_subscription_route,
    connection_key,
    connection_subscription_key,
    gateway_route_key,
    gateway_stream_key,
    user_route_key,
)
from app.core.utils import now_utc

logger = logging.getLogger(__name__)

_CHAT_CHANNEL_RE = re.compile(r"^chat:v\d+:chat:(?P<chat_id>[^:]+):channel$")
_USER_CHANNEL_RE = re.compile(r"^chat:v\d+:user:(?P<user_id>\d+):channel$")


def _decode(value: Any) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def _field(fields: dict[Any, Any], name: str) -> Any:
    return fields.get(name) or fields.get(name.encode("utf-8"))


@dataclass(slots=True)
class ChatConnectionManager:
    redis: Redis
    gateway_id: str = field(default_factory=lambda: os.getenv("GATEWAY_ID") or os.getenv("HOSTNAME", "local-gateway"))
    connections_by_id: dict[str, WSConnection] = field(default_factory=dict)
    connections_by_user: dict[int, set[str]] = field(default_factory=lambda: defaultdict(set))
    subscriptions_by_chat: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _shutdown_event: asyncio.Event = field(default_factory=asyncio.Event)

    @property
    def stream_key(self) -> str:
        return gateway_stream_key(self.gateway_id)

    @property
    def stream_group(self) -> str:
        return f"ws-gateway-{self.gateway_id}"

    @property
    def stream_consumer(self) -> str:
        return f"{self.gateway_id}:{os.getpid()}"

    async def startup(self) -> None:
        self._shutdown_event.clear()
        tasks = [
            asyncio.create_task(self._refresh_routes_loop(), name=f"ws:routes:{self.gateway_id}"),
            asyncio.create_task(self._consume_gateway_stream_loop(), name=f"ws:stream:{self.gateway_id}"),
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        self._shutdown_event.set()
        async with self._lock:
            conns = list(self.connections_by_id.values())

        for conn in conns:
            await self.unregister(conn, close_code=1001, close_reason="server shutdown")

        gateway_connections = await self.redis.smembers(gateway_route_key(self.gateway_id))  # type: ignore[misc]
        if gateway_connections:
            pipe = self.redis.pipeline(transaction=False)
            for raw_cid in gateway_connections:
                pipe.delete(connection_key(_decode(raw_cid)))
            pipe.delete(gateway_route_key(self.gateway_id))
            await pipe.execute()

        logger.info("ChatConnectionManager shut down", extra={"gateway_id": self.gateway_id})

    async def register(self, conn: WSConnection) -> None:
        ws_conn = self._ensure_ws_connection(conn)
        ws_conn.gateway_id = self.gateway_id

        stale_to_close: list[WSConnection] = []
        async with self._lock:
            self.connections_by_id[ws_conn.connection_id] = ws_conn
            user_conns = self.connections_by_user[ws_conn.user_id]
            user_conns.add(ws_conn.connection_id)

            overflow = len(user_conns) - chat_config.WS_MAX_CONNECTIONS_PER_USER
            if overflow > 0:
                stale_to_close.extend(self._oldest_user_connections(user_conns, limit=overflow))

        await self._write_route(ws_conn)
        await ws_conn.start()

        for stale in stale_to_close:
            if stale.connection_id == ws_conn.connection_id:
                continue
            asyncio.create_task(
                self._close_and_unregister(stale, code=1012, reason="connection limit exceeded"),
                name=f"ws:evict:{stale.connection_id}",
            )

        logger.info(
            "WebSocket registered",
            extra={
                "connection_id": ws_conn.connection_id,
                "user_id": ws_conn.user_id,
                "gateway_id": self.gateway_id,
            },
        )

    async def unregister(
        self,
        conn: WSConnection,
        *,
        close_code: int = 1000,
        close_reason: str = "",
    ) -> None:
        ws_conn = self._ensure_ws_connection(conn)

        async with self._lock:
            self.connections_by_id.pop(ws_conn.connection_id, None)
            user_conns = self.connections_by_user.get(ws_conn.user_id)
            if user_conns is not None:
                user_conns.discard(ws_conn.connection_id)
                if not user_conns:
                    self.connections_by_user.pop(ws_conn.user_id, None)

            subscribed_chats = set(ws_conn.subscriptions)
            for chat_id in subscribed_chats:
                self._unsubscribe_chat_in_memory(ws_conn, chat_id)

        await self._delete_route(ws_conn, subscribed_chats)
        await ws_conn.close(code=close_code, reason=close_reason)

        logger.info(
            "WebSocket unregistered",
            extra={
                "connection_id": ws_conn.connection_id,
                "user_id": ws_conn.user_id,
                "gateway_id": self.gateway_id,
                "subscriptions": len(subscribed_chats),
            },
        )

    async def subscribe_chat(self, conn: WSConnection, chat_id: str) -> None:
        ws_conn = self._ensure_ws_connection(conn)
        chat_id = str(chat_id)

        async with self._lock:
            ws_conn.subscriptions.add(chat_id)
            self.subscriptions_by_chat[chat_id].add(ws_conn.connection_id)

        route = active_subscription_route(ws_conn.user_id, self.gateway_id, ws_conn.connection_id)
        pipe = self.redis.pipeline(transaction=False)
        pipe.sadd(active_subscription_key(chat_id), route)
        pipe.expire(active_subscription_key(chat_id), chat_config.WS_ACTIVE_SUBSCRIPTION_TTL)
        pipe.setex(
            connection_subscription_key(ws_conn.connection_id, chat_id),
            chat_config.WS_ACTIVE_SUBSCRIPTION_TTL,
            route,
        )
        await pipe.execute()

    async def unsubscribe_chat(self, conn: WSConnection, chat_id: str) -> None:
        ws_conn = self._ensure_ws_connection(conn)
        chat_id = str(chat_id)

        async with self._lock:
            self._unsubscribe_chat_in_memory(ws_conn, chat_id)

        route = active_subscription_route(ws_conn.user_id, self.gateway_id, ws_conn.connection_id)
        with contextlib.suppress(Exception):
            pipe = self.redis.pipeline(transaction=False)
            pipe.srem(active_subscription_key(chat_id), route)
            pipe.delete(connection_subscription_key(ws_conn.connection_id, chat_id))
            await pipe.execute()

    async def send_to_user_local(self, user_id: int, event: dict[str, Any]) -> None:
        await self.send_to_users_local([user_id], event)

    async def send_to_users_local(
        self,
        user_ids: list[int] | set[int] | tuple[int, ...],
        event: dict[str, Any],
        *,
        chat_id: str | None = None,
        require_subscription: bool = False,
    ) -> None:
        user_id_set = {int(uid) for uid in user_ids}
        async with self._lock:
            conns = [
                conn
                for uid in user_id_set
                for conn_id in tuple(self.connections_by_user.get(uid, ()))
                if (conn := self.connections_by_id.get(conn_id)) is not None
                and (not require_subscription or not chat_id or chat_id in conn.subscriptions)
            ]

        for conn in conns:
            await self._send_or_drop(conn, event)

    async def send_to_chat_local(self, chat_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            conn_ids = tuple(self.subscriptions_by_chat.get(str(chat_id), ()))
            conns = [self.connections_by_id[cid] for cid in conn_ids if cid in self.connections_by_id]

        for conn in conns:
            await self._send_or_drop(conn, event)

    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        event = {**payload, "ts": payload.get("ts") or now_utc().isoformat()}

        if match := _USER_CHANNEL_RE.match(channel):
            await self._enqueue_user_stream_delivery(int(match.group("user_id")), event)
            return

        if match := _CHAT_CHANNEL_RE.match(channel):
            await self.send_to_chat_local(match.group("chat_id"), event)
            return

        logger.warning("Unsupported websocket publish channel", extra={"channel": channel})

    def _oldest_user_connections(self, user_connection_ids: set[str], *, limit: int) -> list[WSConnection]:
        return sorted(
            (
                self.connections_by_id[cid]
                for cid in user_connection_ids
                if cid in self.connections_by_id
            ),
            key=lambda c: c.connected_at,
        )[:limit]

    async def _close_and_unregister(self, conn: WSConnection, code: int, reason: str) -> None:
        await self.unregister(conn, close_code=code, close_reason=reason)

    async def _send_or_drop(self, conn: WSConnection, event: dict[str, Any]) -> None:
        if conn.try_send(event):
            return

        logger.warning(
            "Dropping slow WebSocket consumer",
            extra={"connection_id": conn.connection_id, "user_id": conn.user_id},
        )
        asyncio.create_task(
            self._close_and_unregister(conn, code=1013, reason="slow consumer"),
            name=f"ws:drop:{conn.connection_id}",
        )

    async def _write_route(self, conn: WSConnection) -> None:
        route_value = f"{self.gateway_id}:{conn.connection_id}"
        pipe = self.redis.pipeline(transaction=False)
        pipe.sadd(user_route_key(conn.user_id), route_value)
        pipe.expire(user_route_key(conn.user_id), chat_config.WS_REDIS_CONNECTION_TTL)
        pipe.sadd(gateway_route_key(self.gateway_id), conn.connection_id)
        pipe.expire(gateway_route_key(self.gateway_id), chat_config.WS_REDIS_CONNECTION_TTL)
        pipe.setex(
            connection_key(conn.connection_id),
            chat_config.WS_REDIS_CONNECTION_TTL,
            orjson.dumps(
                {
                    "user_id": conn.user_id,
                    "gateway_id": self.gateway_id,
                    "device_id": conn.device_id,
                    "connected_at": conn.connected_at.isoformat(),
                }
            ),
        )
        await pipe.execute()

    async def _delete_route(self, conn: WSConnection, subscribed_chats: set[str]) -> None:
        route_value = f"{self.gateway_id}:{conn.connection_id}"
        sub_route = active_subscription_route(conn.user_id, self.gateway_id, conn.connection_id)

        pipe = self.redis.pipeline(transaction=False)
        pipe.srem(user_route_key(conn.user_id), route_value)
        pipe.srem(gateway_route_key(self.gateway_id), conn.connection_id)
        pipe.delete(connection_key(conn.connection_id))
        for chat_id in subscribed_chats:
            pipe.srem(active_subscription_key(chat_id), sub_route)
            pipe.delete(connection_subscription_key(conn.connection_id, chat_id))
        await pipe.execute()

    async def _refresh_routes_loop(self) -> None:
        interval = max(5, min(30, chat_config.WS_REDIS_CONNECTION_TTL // 2))
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=float(interval))
                break
            except asyncio.TimeoutError:
                pass

            try:
                await self._refresh_routes()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("WebSocket route refresh failed")

    async def _refresh_routes(self) -> None:
        async with self._lock:
            conns = list(self.connections_by_id.values())
            subs_snapshot = {conn.connection_id: set(conn.subscriptions) for conn in conns}

        for conn in conns:
            if conn.closed:
                await self.unregister(conn)
                continue

            with contextlib.suppress(Exception):
                await self._write_route(conn)

            subscriptions = subs_snapshot.get(conn.connection_id, set())
            if subscriptions:
                with contextlib.suppress(Exception):
                    await self._refresh_subscription_routes(conn, subscriptions)

    async def _refresh_subscription_routes(self, conn: WSConnection, subscriptions: set[str]) -> None:
        route = active_subscription_route(conn.user_id, self.gateway_id, conn.connection_id)
        pipe = self.redis.pipeline(transaction=False)
        for chat_id in subscriptions:
            pipe.sadd(active_subscription_key(chat_id), route)
            pipe.expire(active_subscription_key(chat_id), chat_config.WS_ACTIVE_SUBSCRIPTION_TTL)
            pipe.setex(
                connection_subscription_key(conn.connection_id, chat_id),
                chat_config.WS_ACTIVE_SUBSCRIPTION_TTL,
                route,
            )
        await pipe.execute()

    async def _ensure_gateway_stream_group(self) -> None:
        try:
            await self.redis.xgroup_create(
                name=self.stream_key,
                groupname=self.stream_group,
                id="0-0",
                mkstream=True,
            )
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def _consume_gateway_stream_loop(self) -> None:
        consecutive_errors = 0
        while not self._shutdown_event.is_set():
            try:
                await self._ensure_gateway_stream_group()
                messages = await self.redis.xreadgroup(
                    groupname=self.stream_group,
                    consumername=self.stream_consumer,
                    streams={self.stream_key: ">"},
                    count=chat_config.WS_GATEWAY_STREAM_READ_COUNT,
                    block=chat_config.WS_GATEWAY_STREAM_BLOCK_MS,
                )
                consecutive_errors = 0

                if not messages:
                    continue

                ack_ids: list[Any] = []
                for _stream_name, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        try:
                            await self._handle_gateway_stream_message(fields)
                        except Exception:
                            logger.exception(
                                "Failed to process websocket gateway stream message",
                                extra={"stream_id": _decode(message_id)},
                            )
                        finally:
                            ack_ids.append(message_id)

                if ack_ids:
                    with contextlib.suppress(Exception):
                        await self.redis.xack(self.stream_key, self.stream_group, *ack_ids)

            except asyncio.CancelledError:
                raise
            except Exception:
                consecutive_errors += 1
                backoff = min(consecutive_errors * 0.5, 10.0)
                logger.exception(
                    "WebSocket gateway stream consumer error; retrying in %.1fs",
                    backoff,
                    extra={"gateway_id": self.gateway_id},
                )
                await asyncio.sleep(backoff)

    async def _handle_gateway_stream_message(self, fields: dict[Any, Any]) -> None:
        raw_event = _field(fields, "event")
        raw_user_ids = _field(fields, "user_ids")
        if raw_event is None or raw_user_ids is None:
            return

        event = orjson.loads(raw_event)
        if not isinstance(event, dict):
            return

        user_ids = [int(uid) for uid in orjson.loads(raw_user_ids)]
        chat_id = str(event.get("chat_id") or _decode(_field(fields, "chat_id") or b"")) or None
        require_subscription = bool(event.pop("require_subscription", False))

        await self.send_to_users_local(
            user_ids,
            event,
            chat_id=chat_id,
            require_subscription=require_subscription,
        )

    async def _enqueue_user_stream_delivery(self, user_id: int, event: dict[str, Any]) -> None:
        routes: set[Any] = await self.redis.smembers(user_route_key(user_id))  # type: ignore[misc]
        gateways: set[str] = set()
        for raw in routes or ():
            gateway_id, _sep, connection_id = _decode(raw).partition(":")
            if gateway_id and connection_id:
                gateways.add(gateway_id)

        if not gateways:
            return

        stream_event = {**event, "require_subscription": False}
        pipe = self.redis.pipeline(transaction=False)
        for gateway_id in gateways:
            pipe.xadd(
                gateway_stream_key(gateway_id),
                fields={
                    "event": orjson.dumps(stream_event),
                    "user_ids": orjson.dumps([user_id]),
                    "chat_id": str(stream_event.get("chat_id") or ""),
                },
                maxlen=chat_config.WS_GATEWAY_STREAM_MAXLEN,
                approximate=True,
            )
        await pipe.execute()

    def _unsubscribe_chat_in_memory(self, conn: WSConnection, chat_id: str) -> None:
        conn.subscriptions.discard(chat_id)
        chat_conns = self.subscriptions_by_chat.get(chat_id)
        if chat_conns is None:
            return
        chat_conns.discard(conn.connection_id)
        if not chat_conns:
            self.subscriptions_by_chat.pop(chat_id, None)

    @staticmethod
    def _ensure_ws_connection(conn: WSConnection) -> WSConnection:
        if not isinstance(conn, WSConnection):
            raise TypeError("ChatConnectionManager expects WSConnection instances")
        return conn
