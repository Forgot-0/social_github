from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import orjson
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
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

_MAX_CONSECUTIVE_ERRORS = 5
_BASE_BACKOFF_SECONDS = 1.0
_MAX_BACKOFF_SECONDS = 60.0


@dataclass(slots=True)
class ChatDeliveryRouter:
    redis: Redis
    session_factory: async_sessionmaker[AsyncSession]
    bootstrap_servers: str = field(default_factory=lambda: app_config.BROKER_URL)
    topic: str = field(default_factory=lambda: chat_config.CHAT_TOPIC)
    group_id: str = field(default_factory=lambda: chat_config.DELIVERY_ROUTER_GROUP_ID)
    member_batch_size: int = field(default_factory=lambda: chat_config.DELIVERY_ROUTER_MEMBER_BATCH_SIZE)
    route_lookup_batch_size: int = field(default_factory=lambda: chat_config.DELIVERY_ROUTER_ROUTE_LOOKUP_BATCH_SIZE)
    active_subscriber_scan_batch_size: int = field(
        default_factory=lambda: chat_config.DELIVERY_ROUTER_ACTIVE_SUBSCRIBER_SCAN_BATCH_SIZE
    )
    stream_users_per_entry: int = field(default_factory=lambda: chat_config.WS_GATEWAY_STREAM_USERS_PER_ENTRY)
    stream_maxlen: int = field(default_factory=lambda: chat_config.WS_GATEWAY_STREAM_MAXLEN)

    async def run_forever(self) -> None:
        consecutive_errors = 0
        while True:
            try:
                await self._run_consumer_loop()
                consecutive_errors = 0
            except asyncio.CancelledError:
                raise
            except Exception:
                consecutive_errors += 1
                backoff = min(
                    _BASE_BACKOFF_SECONDS * (2 ** min(consecutive_errors, 10)),
                    _MAX_BACKOFF_SECONDS,
                )
                logger.exception(
                    "Delivery router crashed; restarting in %.1fs",
                    backoff,
                    extra={"consecutive_errors": consecutive_errors},
                )
                await asyncio.sleep(backoff)

    async def _run_consumer_loop(self) -> None:
        consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            max_poll_records=chat_config.DELIVERY_ROUTER_MAX_POLL_RECORDS,
            client_id=chat_config.DELIVERY_ROUTER_CLIENT_ID,
            # Tuning for high throughput
            fetch_max_bytes=52_428_800,   # 50 MB
            max_partition_fetch_bytes=10_485_760,  # 10 MB
            session_timeout_ms=30_000,
            heartbeat_interval_ms=10_000,
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

                t0 = time.monotonic()
                total = 0
                for _tp, messages in records.items():
                    for message in messages:
                        await self._route_raw_message(message.value)  # type: ignore[arg-type]
                        total += 1

                await consumer.commit()
                elapsed = time.monotonic() - t0
                if total:
                    logger.debug(
                        "Batch routed",
                        extra={"messages": total, "elapsed_ms": round(elapsed * 1000)},
                    )
        except asyncio.CancelledError:
            raise
        finally:
            with contextlib.suppress(Exception):
                await consumer.stop()
            logger.info("Chat delivery router stopped")

    # ------------------------------------------------------------------ #
    #  Routing                                                             #
    # ------------------------------------------------------------------ #

    async def _route_raw_message(self, raw_value: bytes) -> None:
        try:
            event = orjson.loads(raw_value)
        except orjson.JSONDecodeError:
            logger.warning("Skipping malformed chat event (invalid JSON)")
            return

        if not isinstance(event, dict) or not is_chat_domain_event(event):
            return

        chat_id = event.get("chat_id")
        if not chat_id:
            logger.warning("Skipping chat event without chat_id", extra={"event_name": event.get("event_name")})
            return

        try:
            await self.route_chat_event(chat_id=str(chat_id), event=event)
        except Exception:
            logger.exception(
                "Failed to route chat event",
                extra={"chat_id": chat_id, "event_id": event.get("event_id")},
            )
            # Don't re-raise: a single bad event must not stop the consumer loop.

    async def route_chat_event(self, chat_id: str, event: dict[str, Any]) -> None:
        ws_event = build_ws_event(event)

        async with self.session_factory() as session:
            chat_repo = ChatRepository(session=session, redis=self.redis)
            chat = await chat_repo.get_by_id(UUID(chat_id))
            if chat is None:
                logger.warning("Skipping event for unknown chat", extra={"chat_id": chat_id})
                return

            strategy = chat.fanout_strategy
            ws_event["fanout_strategy"] = strategy.value

            if strategy == ChatFanoutStrategy.FANOUT_ON_WRITE:
                # Keep DB session open only for the member iteration
                await self._route_fanout_on_write(
                    chat_repo=chat_repo,
                    chat_id=UUID(chat_id),
                    ws_event=ws_event,
                )
                return

        # For ACTIVE_SUBSCRIBERS / CHANNEL_SUBSCRIBERS we must NOT hold
        # a DB session while scanning potentially millions of Redis keys.
        await self._route_to_active_subscribers(chat_id=chat_id, ws_event=ws_event)

    async def _route_fanout_on_write(
        self,
        chat_repo: ChatRepository,
        chat_id: UUID,
        ws_event: dict[str, Any],
    ) -> None:
        """Fan out to every non-banned member that has an online route."""
        tasks: list[asyncio.Task[None]] = []
        async for member_ids in chat_repo.iter_member_ids(
            chat_id=chat_id,
            batch_size=self.member_batch_size,
        ):
            for lookup_batch in chunks(member_ids, self.route_lookup_batch_size):
                routes = await self._lookup_online_routes(lookup_batch)
                if routes:
                    tasks.append(
                        asyncio.create_task(
                            self._enqueue_gateway_deliveries(routes, ws_event, require_subscription=False)
                        )
                    )

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.exception("Gateway delivery task failed", exc_info=r)

    async def _route_to_active_subscribers(
        self, chat_id: str, ws_event: dict[str, Any]
    ) -> None:
        """Fan out only to connections that have explicitly subscribed to this chat."""
        async for routes_by_gateway in self._iter_active_subscriber_routes(chat_id):
            if routes_by_gateway:
                await self._enqueue_gateway_deliveries(
                    routes_by_gateway,
                    ws_event,
                    require_subscription=True,
                )

    # ------------------------------------------------------------------ #
    #  Redis route resolution                                              #
    # ------------------------------------------------------------------ #

    async def _lookup_online_routes(self, user_ids: list[int]) -> RouteMap:
        if not user_ids:
            return {}

        pipe = self.redis.pipeline(transaction=False)
        for user_id in user_ids:
            pipe.smembers(f"ws:route:user:{user_id}")
        results = await pipe.execute()

        routes_by_gateway: RouteMap = {}
        for user_id, route_set in zip(user_ids, results):
            for raw in route_set or ():
                route = _decode(raw)
                gateway_id, _sep, connection_id = route.partition(":")
                if gateway_id and connection_id:
                    routes_by_gateway.setdefault(gateway_id, set()).add(int(user_id))
        return routes_by_gateway

    async def _iter_active_subscriber_routes(self, chat_id: str):
        key = active_subscription_key(chat_id)
        batch: list[ActiveSubscriptionRoute] = []

        async for raw_route in self.redis.sscan_iter(
            key, count=chat_config.WS_ACTIVE_SUBSCRIBER_SCAN_COUNT
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
        for _uid, _gw, connection_id, _route in routes:
            pipe.exists(f"ws:conn:{connection_id}")
        alive_flags = await pipe.execute()

        stale: list[str] = []
        routes_by_gateway: RouteMap = {}
        for (user_id, gateway_id, _conn_id, route), alive in zip(routes, alive_flags):
            if alive:
                routes_by_gateway.setdefault(gateway_id, set()).add(user_id)
            else:
                stale.append(route)

        if stale:
            # Fire-and-forget: stale cleanup is best-effort
            asyncio.create_task(
                self.redis.srem(subscription_key, *stale),  # type: ignore[arg-type]
                name="stale-sub-cleanup",
            )

        return routes_by_gateway

    # ------------------------------------------------------------------ #
    #  Stream enqueueing                                                   #
    # ------------------------------------------------------------------ #

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
            for user_chunk in chunks(sorted(user_ids), self.stream_users_per_entry):
                stream_event = {**ws_event, "ts": ts, "require_subscription": require_subscription}
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
            try:
                await pipe.execute()
            except Exception:
                logger.exception(
                    "Failed to enqueue gateway deliveries",
                    extra={"gateways": list(routes_by_gateway), "enqueued": enqueued},
                )
                raise


def _decode(value: Any) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def gateway_stream_key(gateway_id: str) -> str:
    return f"ws:gateway:{gateway_id}:stream"


def active_subscription_key(chat_id: str) -> str:
    return f"ws:sub:chat:{chat_id}"


def parse_active_subscription_route(raw_route: Any) -> ActiveSubscriptionRoute | None:
    route = _decode(raw_route)
    user_id_str, sep1, rest = route.partition(":")
    gateway_id, sep2, connection_id = rest.partition(":")
    if not sep1 or not sep2 or not user_id_str or not gateway_id or not connection_id:
        return None
    try:
        return int(user_id_str), gateway_id, connection_id, route
    except ValueError:
        return None


async def run_delivery_router(router: ChatDeliveryRouter) -> None:
    with contextlib.suppress(asyncio.CancelledError):
        await router.run_forever()