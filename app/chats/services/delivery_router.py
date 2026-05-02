from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import orjson
from aiokafka import AIOKafkaConsumer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.chats.config import chat_config
from app.chats.dtos.delivery import build_ws_event, chunks, is_chat_domain_event
from app.chats.models.chat import Chat, ChatFanoutStrategy
from app.chats.repositories.chat import ChatRepository
from app.core.configs.app import app_config
from app.core.utils import now_utc

logger = logging.getLogger(__name__)

RouteMap = dict[str, set[int]]
ActiveSubscriptionRoute = tuple[int, str, str, str]


@dataclass(slots=True)
class ChatDeliveryRouter:
    """Kafka -> Redis Streams delivery router for websocket gateways.

    Phase 3 routes by chat fanout policy:

    * direct/group <= 500: fanout-on-write to all online member connections;
    * supergroup and group > 500: online active subscribers only;
    * channel: subscribers are role_id=6, admins/editors are role_id=1/2/3;
      channel posts are delivered to active subscribers while send permission is
      enforced by role in the command layer.
    """

    redis: Redis
    session_factory: async_sessionmaker[AsyncSession]
    bootstrap_servers: str = app_config.BROKER_URL
    topic: str = chat_config.CHAT_TOPIC
    group_id: str = chat_config.DELIVERY_ROUTER_GROUP_ID
    member_batch_size: int = chat_config.DELIVERY_ROUTER_MEMBER_BATCH_SIZE
    route_lookup_batch_size: int = chat_config.DELIVERY_ROUTER_ROUTE_LOOKUP_BATCH_SIZE
    active_subscriber_scan_batch_size: int = chat_config.DELIVERY_ROUTER_ACTIVE_SUBSCRIBER_SCAN_BATCH_SIZE
    stream_users_per_entry: int = chat_config.WS_GATEWAY_STREAM_USERS_PER_ENTRY
    stream_maxlen: int = chat_config.WS_GATEWAY_STREAM_MAXLEN

    async def run_forever(self) -> None:
        consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            max_poll_records=chat_config.DELIVERY_ROUTER_MAX_POLL_RECORDS,
            client_id=chat_config.DELIVERY_ROUTER_CLIENT_ID,
        )
        await consumer.start()
        logger.info(
            "Chat delivery router started",
            extra={"topic": self.topic, "group_id": self.group_id},
        )
        try:
            while True:
                records = await consumer.getmany(
                    timeout_ms=chat_config.DELIVERY_ROUTER_POLL_TIMEOUT_MS,
                    max_records=chat_config.DELIVERY_ROUTER_MAX_POLL_RECORDS,
                )
                if not records:
                    continue

                for _topic_partition, messages in records.items():
                    for message in messages:
                        await self._route_raw_message(message.value) # type: ignore

                await consumer.commit()
        except asyncio.CancelledError:
            raise
        finally:
            await consumer.stop()
            logger.info("Chat delivery router stopped")

    async def _route_raw_message(self, raw_value: bytes) -> None:
        try:
            event = orjson.loads(raw_value)
        except orjson.JSONDecodeError:
            logger.exception("Skipping malformed chat event")
            return

        if not isinstance(event, dict) or not is_chat_domain_event(event):
            return

        chat_id = event.get("chat_id")
        if not chat_id:
            logger.warning("Skipping chat event without chat_id", extra={"event": event})
            return

        try:
            await self.route_chat_event(chat_id=str(chat_id), event=event)
        except Exception:
            logger.exception(
                "Failed to route chat event",
                extra={"chat_id": chat_id, "event_id": event.get("event_id")},
            )
            raise

    async def route_chat_event(self, chat_id: str, event: dict[str, Any]) -> None:
        ws_event = build_ws_event(event)

        async with self.session_factory() as session:
            chat_repo = ChatRepository(session=session, redis=self.redis)
            chat = await chat_repo.get_by_id(UUID(chat_id))
            if chat is None:
                logger.warning("Skipping event for missing chat", extra={"chat_id": chat_id})
                return

            strategy = self._resolve_strategy(chat)
            ws_event["fanout_strategy"] = strategy.value

            if strategy == ChatFanoutStrategy.FANOUT_ON_WRITE:
                await self._route_to_all_online_members(
                    chat_repo=chat_repo,
                    chat_id=UUID(chat_id),
                    ws_event=ws_event,
                    require_subscription=False,
                )
                return

        # Supergroups/channels must not hold a DB transaction while scanning a
        # large Redis active-subscription set.
        await self._route_to_active_subscribers(chat_id=chat_id, ws_event=ws_event)

    def _resolve_strategy(self, chat: Chat) -> ChatFanoutStrategy:
        return chat.fanout_strategy

    async def _route_to_all_online_members(
        self,
        chat_repo: ChatRepository,
        chat_id: UUID,
        ws_event: dict[str, Any],
        *,
        require_subscription: bool,
    ) -> None:
        async for member_ids in chat_repo.iter_member_ids(
            chat_id=chat_id,
            batch_size=self.member_batch_size,
        ):
            for lookup_batch in chunks(member_ids, self.route_lookup_batch_size):
                routes_by_gateway = await self._lookup_online_routes(lookup_batch)
                if routes_by_gateway:
                    await self._enqueue_gateway_deliveries(
                        routes_by_gateway,
                        ws_event,
                        require_subscription=require_subscription,
                    )

    async def _route_to_active_subscribers(self, chat_id: str, ws_event: dict[str, Any]) -> None:
        async for routes_by_gateway in self._iter_active_subscriber_routes(chat_id):
            if routes_by_gateway:
                await self._enqueue_gateway_deliveries(
                    routes_by_gateway,
                    ws_event,
                    require_subscription=True,
                )

    async def _lookup_online_routes(self, user_ids: list[int]) -> RouteMap:
        if not user_ids:
            return {}

        pipe = self.redis.pipeline(transaction=False)
        for user_id in user_ids:
            pipe.smembers(f"ws:route:user:{user_id}")
        route_sets = await pipe.execute()

        routes_by_gateway: RouteMap = {}
        for user_id, route_values in zip(user_ids, route_sets, strict=False):
            for raw_route in route_values or ():
                route = _decode(raw_route)
                gateway_id, _sep, connection_id = route.partition(":")
                if not gateway_id or not connection_id:
                    continue
                routes_by_gateway.setdefault(gateway_id, set()).add(int(user_id))
        return routes_by_gateway

    async def _iter_active_subscriber_routes(self, chat_id: str):
        key = active_subscription_key(chat_id)
        batch: list[ActiveSubscriptionRoute] = []

        async for raw_route in self.redis.sscan_iter(
            key,
            count=chat_config.WS_ACTIVE_SUBSCRIBER_SCAN_COUNT,
        ):
            parsed = parse_active_subscription_route(raw_route)
            if parsed is None:
                continue
            batch.append(parsed)
            if len(batch) >= self.active_subscriber_scan_batch_size:
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
            pipe.exists(f"ws:conn:{connection_id}")
        alive_flags = await pipe.execute()

        stale_routes: list[str] = []
        routes_by_gateway: RouteMap = {}
        for (user_id, gateway_id, _connection_id, route), alive in zip(routes, alive_flags, strict=False):
            if alive:
                routes_by_gateway.setdefault(gateway_id, set()).add(user_id)
            else:
                stale_routes.append(route)

        if stale_routes:
            await self.redis.srem(subscription_key, *stale_routes) # type: ignore

        return routes_by_gateway

    async def _enqueue_gateway_deliveries(
        self,
        routes_by_gateway: RouteMap,
        ws_event: dict[str, Any],
        *,
        require_subscription: bool,
    ) -> None:
        pipe = self.redis.pipeline(transaction=False)
        enqueued = 0
        ts = ws_event.get("ts") or now_utc().isoformat()
        for gateway_id, user_ids in routes_by_gateway.items():
            stream_key = gateway_stream_key(gateway_id)
            for user_chunk in chunks(sorted(user_ids), self.stream_users_per_entry):
                stream_event = dict(ws_event)
                stream_event.setdefault("ts", ts)
                stream_event["require_subscription"] = require_subscription
                pipe.xadd(
                    stream_key,
                    fields={
                        "event": orjson.dumps(stream_event),
                        "user_ids": orjson.dumps(user_chunk),
                        "chat_id": str(ws_event.get("chat_id") or ""),
                    },
                    maxlen=self.stream_maxlen,
                    approximate=True,
                )
                enqueued += 1

        if enqueued:
            await pipe.execute()


def _decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def gateway_stream_key(gateway_id: str) -> str:
    return f"ws:gateway:{gateway_id}:stream"


def active_subscription_key(chat_id: str) -> str:
    return f"ws:sub:chat:{chat_id}"


def parse_active_subscription_route(raw_route: Any) -> ActiveSubscriptionRoute | None:
    route = _decode(raw_route)
    user_id, sep1, rest = route.partition(":")
    gateway_id, sep2, connection_id = rest.partition(":")
    if not sep1 or not sep2 or not user_id or not gateway_id or not connection_id:
        return None
    try:
        return int(user_id), gateway_id, connection_id, route
    except ValueError:
        return None


async def run_delivery_router(router: ChatDeliveryRouter) -> None:
    with contextlib.suppress(asyncio.CancelledError):
        await router.run_forever()
