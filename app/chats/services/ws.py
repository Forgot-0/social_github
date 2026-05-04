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
from app.chats.services.delivery_router import gateway_stream_key
from app.core.utils import now_utc
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)

_CHAT_CHANNEL_RE = re.compile(r"^chat:v\d+:chat:(?P<chat_id>[^:]+):channel$")
_USER_CHANNEL_RE = re.compile(r"^chat:v\d+:user:(?P<user_id>\d+):channel$")


def _decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _field(fields: dict[Any, Any], name: str) -> Any:
    return fields.get(name) or fields.get(name.encode("utf-8"))


def _sub_route_value(user_id: int, gateway_id: str, connection_id: str) -> str:
    return f"{user_id}:{gateway_id}:{connection_id}"


@dataclass
class ChatConnectionManager(BaseConnectionManager):
    redis: Redis
    gateway_id: str = field(
        default_factory=lambda: os.getenv("GATEWAY_ID") or os.getenv("HOSTNAME", "local-gateway")
    )

    connections_by_id: dict[str, WSConnection] = field(default_factory=dict)
    connections_by_user: dict[int, set[str]] = field(default_factory=lambda: defaultdict(set))
    subscriptions_by_chat: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

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
        tasks = [
            asyncio.create_task(
                self._refresh_routes_loop(), name=f"ws:routes:{self.gateway_id}"
            ),
            asyncio.create_task(
                self._consume_gateway_stream_loop(), name=f"ws:stream:{self.gateway_id}"
            ),
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        for conn in list(self.connections_by_id.values()):
            await self.unregister(conn)

    async def register(self, conn: WSConnection) -> None:
        stale_to_close: list[WSConnection] = []
        async with self._lock:
            self.connections_by_id[conn.connection_id] = conn
            user_connections = self.connections_by_user[conn.user_id]
            user_connections.add(conn.connection_id)

            overflow = len(user_connections) - chat_config.WS_MAX_CONNECTIONS_PER_USER
            if overflow > 0:
                oldest = sorted(
                    (
                        self.connections_by_id[cid]
                        for cid in user_connections
                        if cid in self.connections_by_id
                    ),
                    key=lambda c: c.connected_at,
                )[:overflow]
                stale_to_close.extend(oldest)

        await self._write_route(conn)
        await conn.start()

        for stale in stale_to_close:
            if stale.connection_id != conn.connection_id:
                await stale.close(code=1012, reason="connection limit exceeded")
                await self.unregister(stale)

        logger.info(
            "WebSocket registered",
            extra={
                "connection_id": conn.connection_id,
                "user_id": conn.user_id,
                "gateway_id": self.gateway_id,
            },
        )

    async def unregister(self, conn: WSConnection) -> None:
        subscribed_chats: set[str] = set()
        async with self._lock:
            self.connections_by_id.pop(conn.connection_id, None)
            user_connections = self.connections_by_user.get(conn.user_id)
            if user_connections is not None:
                user_connections.discard(conn.connection_id)
                if not user_connections:
                    self.connections_by_user.pop(conn.user_id, None)

            subscribed_chats = set(conn.subscriptions)
            for chat_id in list(conn.subscriptions):
                self._unsubscribe_chat_in_memory(conn, chat_id)

        route_value = f"{self.gateway_id}:{conn.connection_id}"
        pipe = self.redis.pipeline(transaction=False)
        pipe.srem(f"ws:route:user:{conn.user_id}", route_value)
        pipe.srem(f"ws:route:gateway:{self.gateway_id}", conn.connection_id)
        pipe.delete(f"ws:conn:{conn.connection_id}")

        if subscribed_chats:
            sub_route = _sub_route_value(conn.user_id, self.gateway_id, conn.connection_id)
            for chat_id in subscribed_chats:
                pipe.srem(f"ws:sub:chat:{chat_id}", sub_route)

        await pipe.execute()
        await conn.close()

        logger.info(
            "WebSocket unregistered",
            extra={
                "connection_id": conn.connection_id,
                "user_id": conn.user_id,
                "gateway_id": self.gateway_id,
            },
        )

    async def subscribe_chat(self, conn: WSConnection, chat_id: str) -> None:
        async with self._lock:
            conn.subscriptions.add(chat_id)
            self.subscriptions_by_chat[chat_id].add(conn.connection_id)

        sub_route = _sub_route_value(conn.user_id, self.gateway_id, conn.connection_id)
        await self.redis.sadd(f"ws:sub:chat:{chat_id}", sub_route)  # type: ignore[misc]
        await self.redis.expire(
            f"ws:sub:chat:{chat_id}", chat_config.WS_ACTIVE_SUBSCRIPTION_TTL
        )

    async def unsubscribe_chat(self, conn: WSConnection, chat_id: str) -> None:
        """Remove subscription both in-memory and in Redis."""
        async with self._lock:
            self._unsubscribe_chat_in_memory(conn, chat_id)

        sub_route = _sub_route_value(conn.user_id, self.gateway_id, conn.connection_id)
        await self.redis.srem(f"ws:sub:chat:{chat_id}", sub_route)  # type: ignore[misc]

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
            conns: list[WSConnection] = []
            for uid in user_id_set:
                for conn_id in tuple(self.connections_by_user.get(uid, ())):
                    conn = self.connections_by_id.get(conn_id)
                    if conn is None:
                        continue
                    if require_subscription and chat_id and chat_id not in conn.subscriptions:
                        continue
                    conns.append(conn)

        for conn in conns:
            await self._send_or_drop(conn, event)

    async def send_to_chat_local(self, chat_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            conn_ids = tuple(self.subscriptions_by_chat.get(chat_id, ()))
            conns = [
                self.connections_by_id[cid]
                for cid in conn_ids
                if cid in self.connections_by_id
            ]

        for conn in conns:
            await self._send_or_drop(conn, event)

    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        event = dict(payload)
        event.setdefault("ts", now_utc().isoformat())

        user_match = _USER_CHANNEL_RE.match(channel)
        if user_match:
            await self._enqueue_user_stream_delivery(int(user_match.group("user_id")), event)
            return

        chat_match = _CHAT_CHANNEL_RE.match(channel)
        if chat_match:
            await self.send_to_chat_local(chat_match.group("chat_id"), event)
            return

        logger.warning("Unsupported websocket publish channel", extra={"channel": channel})


    async def _send_or_drop(self, conn: WSConnection, event: dict[str, Any]) -> None:
        ok = conn.try_send(event)
        if ok:
            return

        logger.warning(
            "Dropping slow WebSocket consumer",
            extra={"connection_id": conn.connection_id, "user_id": conn.user_id},
        )
        await conn.close(code=1013, reason="slow consumer")
        await self.unregister(conn)

    async def _write_route(self, conn: WSConnection) -> None:
        route_value = f"{self.gateway_id}:{conn.connection_id}"
        user_route_key = f"ws:route:user:{conn.user_id}"
        gateway_route_key = f"ws:route:gateway:{self.gateway_id}"
        pipe = self.redis.pipeline(transaction=False)
        pipe.sadd(user_route_key, route_value)
        pipe.expire(user_route_key, chat_config.WS_REDIS_CONNECTION_TTL)
        pipe.sadd(gateway_route_key, conn.connection_id)
        pipe.expire(gateway_route_key, chat_config.WS_REDIS_CONNECTION_TTL)
        pipe.setex(
            f"ws:conn:{conn.connection_id}",
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

    async def _refresh_routes_loop(self) -> None:
        interval = max(5, min(30, chat_config.WS_REDIS_CONNECTION_TTL // 2))
        while True:
            await asyncio.sleep(interval)
            await self._refresh_routes()

    async def _refresh_routes(self) -> None:
        async with self._lock:
            conns = list(self.connections_by_id.values())
            subs_snapshot: dict[str, set[str]] = {
                conn.connection_id: set(conn.subscriptions) for conn in conns
            }

        for conn in conns:
            if conn.closed:
                await self.unregister(conn)
                continue

            with contextlib.suppress(Exception):
                await self._write_route(conn)

            conn_subs = subs_snapshot.get(conn.connection_id, set())
            if not conn_subs:
                continue

            sub_route = _sub_route_value(conn.user_id, self.gateway_id, conn.connection_id)
            pipe = self.redis.pipeline(transaction=False)
            for chat_id in conn_subs:
                pipe.sadd(f"ws:sub:chat:{chat_id}", sub_route)
                pipe.expire(
                    f"ws:sub:chat:{chat_id}", chat_config.WS_ACTIVE_SUBSCRIPTION_TTL
                )
            with contextlib.suppress(Exception):
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
        while True:
            try:
                await self._ensure_gateway_stream_group()
                messages = await self.redis.xreadgroup(
                    groupname=self.stream_group,
                    consumername=self.stream_consumer,
                    streams={self.stream_key: ">"},
                    count=chat_config.WS_GATEWAY_STREAM_READ_COUNT,
                    block=chat_config.WS_GATEWAY_STREAM_BLOCK_MS,
                )
                if not messages:
                    continue

                for _stream_name, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        try:
                            await self._handle_gateway_stream_message(fields)
                        except Exception:
                            logger.exception(
                                "Failed to process gateway stream message",
                                extra={
                                    "gateway_id": self.gateway_id,
                                    "stream_id": _decode(message_id),
                                },
                            )
                        finally:
                            with contextlib.suppress(Exception):
                                await self.redis.xack(
                                    self.stream_key, self.stream_group, message_id
                                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Gateway stream consumer failed; retrying",
                    extra={"gateway_id": self.gateway_id},
                )
                await asyncio.sleep(1)

    async def _handle_gateway_stream_message(self, fields: dict[Any, Any]) -> None:
        raw_event = _field(fields, "event")
        raw_user_ids = _field(fields, "user_ids")
        if raw_event is None or raw_user_ids is None:
            return

        event = orjson.loads(raw_event)
        user_ids = [int(uid) for uid in orjson.loads(raw_user_ids)]
        chat_id = (
            str(event.get("chat_id") or _decode(_field(fields, "chat_id") or "")) or None
        )
        require_subscription = bool(event.pop("require_subscription", False))

        await self.send_to_users_local(
            user_ids,
            event,
            chat_id=chat_id,
            require_subscription=require_subscription,
        )

    async def _enqueue_user_stream_delivery(self, user_id: int, event: dict[str, Any]) -> None:
        routes = await self.redis.smembers(f"ws:route:user:{user_id}")  # type: ignore
        gateways: set[str] = set()
        for raw_route in routes or ():
            route = _decode(raw_route)
            gateway_id, _sep, connection_id = route.partition(":")
            if gateway_id and connection_id:
                gateways.add(gateway_id)

        if not gateways:
            return

        stream_event = dict(event)
        stream_event["require_subscription"] = False
        pipe = self.redis.pipeline(transaction=False)
        for gw_id in gateways:
            pipe.xadd(
                gateway_stream_key(gw_id),
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
        chat_connections = self.subscriptions_by_chat.get(chat_id)
        if chat_connections is None:
            return
        chat_connections.discard(conn.connection_id)
        if not chat_connections:
            self.subscriptions_by_chat.pop(chat_id, None)
