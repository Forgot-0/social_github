from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import orjson
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.chats.config import chat_config
from app.chats.dtos.delivery import build_ws_event, chunks, is_chat_domain_event
from app.chats.models.chat import ChatFanoutStrategy
from app.chats.repositories.chat import ChatRepository
from app.core.utils import now_utc

logger = logging.getLogger(__name__)

RouteMap = dict[str, set[int]]
ActiveSubscriptionRoute = tuple[int, str, str, str]


@dataclass(slots=True)
class ChatDeliveryRouter:
    redis: Redis
    chat_repository: ChatRepository

    async def route_broker_message(self, message: dict[str, Any] | bytes | bytearray | str) -> None:
        event = self._decode_event(message)
        if event is None or not is_chat_domain_event(event):
            return

        chat_id = event.get("chat_id")
        if not chat_id:
            logger.warning(
                "Skipping chat event without chat_id",
                extra={"event_name": event.get("event_name"), "event_id": event.get("event_id")},
            )
            return

        try:
            await self.route_chat_event(chat_id=str(chat_id), event=event)
        except Exception:
            logger.exception(
                "Failed to route chat event",
                extra={"chat_id": chat_id, "event_id": event.get("event_id")},
            )

    async def route_raw_message(self, raw_value: bytes) -> None:
        await self.route_broker_message(raw_value)

    async def route_chat_event(self, chat_id: str, event: dict[str, Any]) -> None:
        ws_event = build_ws_event(event)

        chat = await self.chat_repository.get_by_id(UUID(chat_id))
        if chat is None:
            logger.warning("Skipping event for unknown chat", extra={"chat_id": chat_id})
            return

        strategy = chat.fanout_strategy
        ws_event["fanout_strategy"] = strategy.value

        if strategy == ChatFanoutStrategy.FANOUT_ON_WRITE:
            await self._route_fanout_on_write(
                chat_repo=self.chat_repository,
                chat_id=UUID(chat_id),
                ws_event=ws_event,
            )
            return

        await self._route_to_active_subscribers(chat_id=chat_id, ws_event=ws_event)

    async def _route_fanout_on_write(
        self,
        chat_repo: ChatRepository,
        chat_id: UUID,
        ws_event: dict[str, Any],
    ) -> None:
        async for member_ids in chat_repo.iter_member_ids(
            chat_id=chat_id,
            batch_size=chat_config.DELIVERY_ROUTER_MEMBER_BATCH_SIZE,
        ):
            for lookup_batch in chunks(member_ids, chat_config.DELIVERY_ROUTER_ROUTE_LOOKUP_BATCH_SIZE):
                routes = await self._lookup_online_routes(lookup_batch)
                await self._enqueue_gateway_deliveries(
                    routes,
                    ws_event,
                    require_subscription=False,
                )

    async def _route_to_active_subscribers(self, chat_id: str, ws_event: dict[str, Any]) -> None:
        async for routes_by_gateway in self._iter_active_subscriber_routes(chat_id):
            await self._enqueue_gateway_deliveries(
                routes_by_gateway,
                ws_event,
                require_subscription=True,
            )

    async def _lookup_online_routes(self, user_ids: Iterable[int]) -> RouteMap:
        ids = [int(user_id) for user_id in user_ids]
        if not ids:
            return {}

        pipe = self.redis.pipeline(transaction=False)
        for user_id in ids:
            pipe.smembers(user_route_key(user_id))
        results = await pipe.execute()

        routes_by_gateway: RouteMap = {}
        stale_routes_by_user: list[tuple[int, str]] = []

        for user_id, route_set in zip(ids, results):
            for raw in route_set or ():
                route = _decode(raw)
                gateway_id, sep, connection_id = route.partition(ROUTE_SEPARATOR)
                if not sep or not gateway_id or not connection_id:
                    stale_routes_by_user.append((user_id, route))
                    continue
                routes_by_gateway.setdefault(gateway_id, set()).add(user_id)

        if stale_routes_by_user:
            asyncio.create_task(
                self._cleanup_stale_user_routes(stale_routes_by_user),
                name="ws:route:cleanup:user",
            )

        return routes_by_gateway

    async def _iter_active_subscriber_routes(self, chat_id: str) -> AsyncIterator[RouteMap]:
        key = active_subscription_key(chat_id)
        batch: list[ActiveSubscriptionRoute] = []

        async for raw_route in self.redis.sscan_iter(key, count=chat_config.WS_ACTIVE_SUBSCRIBER_SCAN_COUNT):
            parsed = parse_active_subscription_route(raw_route)
            if parsed is None:
                with contextlib.suppress(Exception):
                    await self.redis.srem(key, raw_route) # type: ignore
                continue

            batch.append(parsed)
            if len(batch) >= chat_config.DELIVERY_ROUTER_ACTIVE_SUBSCRIBER_SCAN_BATCH_SIZE:
                yield await self._validate_active_subscriber_batch(key, batch)
                batch = []

        if batch:
            yield await self._validate_active_subscriber_batch(key, batch)

    async def _validate_active_subscriber_batch(
        self,
        subscription_key: str,
        routes: list[ActiveSubscriptionRoute],
    ) -> RouteMap:
        pipe = self.redis.pipeline(transaction=False)
        for _user_id, _gateway_id, connection_id, _route in routes:
            pipe.exists(connection_key(connection_id))
        alive_flags = await pipe.execute()

        stale: list[str] = []
        routes_by_gateway: RouteMap = {}
        for (user_id, gateway_id, _connection_id, route), alive in zip(routes, alive_flags):
            if alive:
                routes_by_gateway.setdefault(gateway_id, set()).add(user_id)
            else:
                stale.append(route)

        if stale:
            asyncio.create_task(
                self.redis.srem(subscription_key, *stale),  # type: ignore[arg-type]
                name="ws:sub:cleanup:stale",
            )

        return routes_by_gateway

    async def _enqueue_gateway_deliveries(
        self,
        routes_by_gateway: RouteMap,
        ws_event: dict[str, Any],
        *,
        require_subscription: bool,
    ) -> None:
        if not routes_by_gateway:
            return

        ts = ws_event.get("ts") or now_utc().isoformat()
        pipe = self.redis.pipeline(transaction=False)
        enqueued = 0

        for gateway_id, user_ids in routes_by_gateway.items():
            stream_key = gateway_stream_key(gateway_id)
            for user_chunk in chunks(sorted(user_ids), chat_config.WS_GATEWAY_STREAM_USERS_PER_ENTRY):
                stream_event = {
                    **ws_event,
                    "ts": ts,
                    "require_subscription": require_subscription,
                }
                pipe.xadd(
                    stream_key,
                    fields={
                        "event": orjson.dumps(stream_event),
                        "user_ids": orjson.dumps(user_chunk),
                        "chat_id": str(ws_event.get("chat_id") or ""),
                    },
                    maxlen=chat_config.WS_GATEWAY_STREAM_MAXLEN,
                    approximate=True,
                )
                enqueued += 1

        if not enqueued:
            return

        try:
            await pipe.execute()
        except Exception:
            logger.exception(
                "Failed to enqueue websocket gateway deliveries",
                extra={"gateways": list(routes_by_gateway), "enqueued": enqueued},
            )
            raise

    async def _cleanup_stale_user_routes(self, stale_routes_by_user: list[tuple[int, str]]) -> None:
        pipe = self.redis.pipeline(transaction=False)
        for user_id, route in stale_routes_by_user:
            pipe.srem(user_route_key(user_id), route)
        with contextlib.suppress(Exception):
            await pipe.execute()

    @staticmethod
    def _decode_event(message: dict[str, Any] | bytes | bytearray | str) -> dict[str, Any] | None:
        if isinstance(message, dict):
            return message

        try:
            decoded = orjson.loads(message)
        except orjson.JSONDecodeError:
            logger.warning("Skipping malformed chat event: invalid JSON")
            return None

        if not isinstance(decoded, dict):
            logger.warning("Skipping malformed chat event: expected JSON object")
            return None
        return decoded


ROUTE_SEPARATOR = ":"


def _decode(value: Any) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def user_route_key(user_id: int) -> str:
    return f"ws:route:user:{int(user_id)}"


def gateway_route_key(gateway_id: str) -> str:
    return f"ws:route:gateway:{gateway_id}"


def connection_key(connection_id: str) -> str:
    return f"ws:conn:{connection_id}"


def gateway_stream_key(gateway_id: str) -> str:
    return f"ws:gateway:{gateway_id}:stream"


def active_subscription_key(chat_id: str) -> str:
    return f"ws:sub:chat:{chat_id}"


def connection_subscription_key(connection_id: str, chat_id: str) -> str:
    return f"ws:sub:conn:{connection_id}:{chat_id}"


def active_subscription_route(user_id: int, gateway_id: str, connection_id: str) -> str:
    return f"{int(user_id)}{ROUTE_SEPARATOR}{gateway_id}{ROUTE_SEPARATOR}{connection_id}"


def parse_active_subscription_route(raw_route: Any) -> ActiveSubscriptionRoute | None:
    route = _decode(raw_route)
    user_id_str, sep1, rest = route.partition(ROUTE_SEPARATOR)
    gateway_id, sep2, connection_id = rest.partition(ROUTE_SEPARATOR)
    if not sep1 or not sep2 or not user_id_str or not gateway_id or not connection_id:
        return None
    try:
        return int(user_id_str), gateway_id, connection_id, route
    except ValueError:
        return None
