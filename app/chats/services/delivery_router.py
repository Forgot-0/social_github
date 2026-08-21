import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Iterable
from dataclasses import asdict, dataclass
from uuid import UUID

import orjson
from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.dtos.delivery import WsEvent, chunks, is_chat_domain_event
from app.chats.keys import WebsocketKeys
from app.chats.metrics import (
    DELIVERY_ROUTER_OFFLINE_RECIPIENTS,
    DELIVERY_ROUTER_OFFLINE_SIGNALS,
    DELIVERY_ROUTER_STREAM_ENTRIES,
)
from app.chats.models.chat import ChatFanoutStrategy
from app.chats.repositories.chat import ChatRepository
from app.core.consumers.event import DictEventDTO
from app.core.message_brokers.base import BaseMessageBroker

logger = logging.getLogger(__name__)

RouteMap = dict[str, set[int]]
ActiveSubscriptionRoute = tuple[int, str, str, str]

OFFLINE_SIGNAL_EVENT_NAMES: frozenset[str] = frozenset({"chats.message.sent"})


@dataclass(slots=True)
class ChatDeliveryRouter:
    redis: Redis
    chat_repository: ChatRepository
    broker: BaseMessageBroker

    async def route_broker_message(self, event: DictEventDTO) -> None:
        if event is None or not is_chat_domain_event(event.event_name):
            return

        chat_id = event.payload.get("chat_id")
        if not chat_id:
            logger.warning(
                "Skipping chat event without chat_id",
                extra={"event_name": event.event_name, "event_id": str(event.event_id)},
            )
            return

        try:
            await self.route_chat_event(chat_id=str(chat_id), event=event)
        except Exception:
            logger.exception(
                "Failed to route chat event",
                extra={"chat_id": chat_id, "event_id": str(event.event_id)},
            )

    async def route_chat_event(self, chat_id: str, event: DictEventDTO) -> None:

        chat = await self.chat_repository.get_by_id(UUID(chat_id))
        if chat is None:
            logger.warning("Skipping event for unknown chat", extra={"chat_id": chat_id})
            return

        ws_event = WsEvent.build(event, fanout_strategy=chat.fanout_strategy)

        if ws_event.fanout_strategy == ChatFanoutStrategy.FANOUT_ON_WRITE:
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
        ws_event: WsEvent,
    ) -> None:
        async for member_ids in chat_repo.iter_member_ids(
            chat_id=chat_id,
            batch_size=chat_config.DELIVERY_ROUTER_MEMBER_BATCH_SIZE,
        ):
            for lookup_batch in chunks(member_ids, chat_config.DELIVERY_ROUTER_ROUTE_LOOKUP_BATCH_SIZE):
                routes = await self._lookup_online_routes(lookup_batch)

                await self._publish_offline_signal(
                    chat_id=chat_id,
                    ws_event=ws_event,
                    lookup_batch=lookup_batch,
                    routes=routes,
                )

                await self._enqueue_gateway_deliveries(
                    routes,
                    ws_event,
                    require_subscription=False,
                )

    async def _route_to_active_subscribers(self, chat_id: str, ws_event: WsEvent) -> None:
        async for routes_by_gateway in self._iter_active_subscriber_routes(chat_id):
            await self._enqueue_gateway_deliveries(
                routes_by_gateway,
                ws_event,
                require_subscription=True,
            )

    async def _publish_offline_signal(
        self,
        chat_id: UUID,
        ws_event: WsEvent,
        lookup_batch: Iterable[int],
        routes: RouteMap,
    ) -> None:
        if ws_event.event_name not in OFFLINE_SIGNAL_EVENT_NAMES:
            return

        online_user_ids: set[int] = set()
        for gateway_users in routes.values():
            online_user_ids |= gateway_users

        offline_user_ids = sorted(set(lookup_batch) - online_user_ids)
        if not offline_user_ids:
            return

        payload = ws_event.payload
        message_id = payload.get("message_id")
        sender_id = payload.get("sender_id")

        data = {
            "event_id": ws_event.event_id,
            "event_name": ws_event.event_name,
            "chat_id": str(chat_id),
            "message_id": str(message_id) if message_id is not None else None,
            "sender_id": int(sender_id) if sender_id is not None else None,
            "offline_user_ids": offline_user_ids,
            "occurred_at": ws_event.ts,
        }

        try:
            await self.broker.send_data(
                key=str(chat_id),
                topic=chat_config.CHAT_OFFLINE_DELIVERY_TOPIC,
                data=data,
            )
        except Exception:
            DELIVERY_ROUTER_OFFLINE_SIGNALS.labels(result="error").inc()
            logger.exception(
                "Failed to publish offline delivery signal",
                extra={
                    "chat_id": str(chat_id),
                    "event_id": data["event_id"],
                    "offline_recipients": len(offline_user_ids),
                },
            )
            return

        DELIVERY_ROUTER_OFFLINE_SIGNALS.labels(result="ok").inc()
        DELIVERY_ROUTER_OFFLINE_RECIPIENTS.inc(len(offline_user_ids))

    async def _lookup_online_routes(self, user_ids: Iterable[int]) -> RouteMap:
        ids = [int(user_id) for user_id in user_ids]
        if not ids:
            return {}

        pipe = self.redis.pipeline(transaction=False)
        for user_id in ids:
            pipe.smembers(WebsocketKeys.user_route_key(user_id))
        results = await pipe.execute()

        routes_by_gateway: RouteMap = {}
        stale_routes_by_user: list[tuple[int, str]] = []

        for user_id, route_set in zip(ids, results, strict=False):
            for route in route_set or ():
                gateway_id, sep, connection_id = route.partition(":")
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
        key = WebsocketKeys.active_subscription_key(chat_id)
        batch: list[ActiveSubscriptionRoute] = []

        async for route in self.redis.sscan_iter(key, count=chat_config.WS_ACTIVE_SUBSCRIBER_SCAN_COUNT):
            parsed = parse_active_subscription_route(route)
            if parsed is None:
                with contextlib.suppress(Exception):
                    await self.redis.srem(key, route)
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
            pipe.exists(WebsocketKeys.connection_key(connection_id))
        alive_flags = await pipe.execute()

        stale: list[str] = []
        routes_by_gateway: RouteMap = {}
        for (user_id, gateway_id, _connection_id, route), alive in zip(routes, alive_flags, strict=False):
            if alive:
                routes_by_gateway.setdefault(gateway_id, set()).add(user_id)
            else:
                stale.append(route)

        if stale:
            asyncio.create_task(
                self.redis.srem(subscription_key, *stale), # pyright: ignore[reportArgumentType]
                name="ws:sub:cleanup:stale",
            )

        return routes_by_gateway

    async def _enqueue_gateway_deliveries(
        self,
        routes_by_gateway: RouteMap,
        ws_event: WsEvent,
        *,
        require_subscription: bool,
    ) -> None:
        if not routes_by_gateway:
            return

        pipe = self.redis.pipeline(transaction=False)
        enqueued = 0

        for gateway_id, user_ids in routes_by_gateway.items():
            stream_key = WebsocketKeys.gateway_stream_key(gateway_id)
            for user_chunk in chunks(sorted(user_ids), chat_config.WS_GATEWAY_STREAM_USERS_PER_ENTRY):
                stream_event = {
                    **asdict(ws_event),
                    "ts": ws_event.ts,
                    "require_subscription": require_subscription,
                }
                pipe.xadd(
                    stream_key,
                    fields={
                        "event": orjson.dumps(stream_event),
                        "user_ids": orjson.dumps(user_chunk),
                        "chat_id": str(ws_event.chat_id),
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

        DELIVERY_ROUTER_STREAM_ENTRIES.labels(strategy=ws_event.fanout_strategy.value).inc(enqueued)

    async def _cleanup_stale_user_routes(self, stale_routes_by_user: list[tuple[int, str]]) -> None:
        pipe = self.redis.pipeline(transaction=False)
        for user_id, route in stale_routes_by_user:
            pipe.srem(WebsocketKeys.user_route_key(user_id), route)
        with contextlib.suppress(Exception):
            await pipe.execute()


def parse_active_subscription_route(route: str) -> ActiveSubscriptionRoute | None:
    user_id_str, sep1, rest = route.partition(":")
    gateway_id, sep2, connection_id = rest.partition(":")
    if not sep1 or not sep2 or not user_id_str or not gateway_id or not connection_id:
        return None
    try:
        return int(user_id_str), gateway_id, connection_id, route
    except ValueError:
        return None

