import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from uuid import UUID

import orjson
from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.dtos.chats import ChatDTO
from app.chats.dtos.delivery import WsEvent, chunks
from app.chats.dtos.messages import MessageDTO
from app.chats.keys import WebsocketKeys
from app.chats.metrics import (
    DELIVERY_ROUTER_OFFLINE_RECIPIENTS,
    DELIVERY_ROUTER_OFFLINE_SIGNALS,
    DELIVERY_ROUTER_STREAM_ENTRIES,
)
from app.chats.models.chat import ChatFanoutStrategy
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.schemas.ws import ChatEventPayload
from app.core.consumers.event import TypedEventDTO
from app.core.message_brokers.base import BaseMessageBroker

logger = logging.getLogger(__name__)

RouteMap = dict[str, set[int]]
ActiveSubscriptionRoute = tuple[int, str, str, str]

OFFLINE_SIGNAL_EVENT_NAMES: frozenset[str] = frozenset({"chats.message.sent"})


@dataclass
class ChatDeliveryRouter:
    redis: Redis
    chat_repository: ChatRepository
    message_repository: MessageRepository
    broker: BaseMessageBroker

    async def route_broker_message(self, event: TypedEventDTO[ChatEventPayload]) -> None:

        chat = await self.chat_repository.get_by_id(event.payload.chat_id)
        if chat is None:
            return

        ws_event = WsEvent.build(event, fanout_strategy=chat.fanout_strategy)
        message = await self.message_repository.get_by_id(
            ws_event.payload.message_id, for_offline=True
        )
        if message is None:
            return

        if ws_event.fanout_strategy == ChatFanoutStrategy.FANOUT_ON_WRITE:
            await self._route_fanout_on_write(
                chat=ChatDTO.model_validate(chat),
                ws_event=ws_event,
                message=MessageDTO.model_validate(message)
            )
            return

        await self._route_to_active_subscribers(
            chat=ChatDTO.model_validate(chat),
            ws_event=ws_event,
            message=MessageDTO.model_validate(message)
        )

    async def _route_fanout_on_write(
        self,
        chat: ChatDTO,
        ws_event: WsEvent,
        message: MessageDTO,
    ) -> None:
        async for member_ids in self.chat_repository.iter_member_ids(
            chat_id=chat.id,
            batch_size=chat_config.DELIVERY_ROUTER_MEMBER_BATCH_SIZE,
        ):
            for lookup_batch in chunks(member_ids, chat_config.DELIVERY_ROUTER_ROUTE_LOOKUP_BATCH_SIZE):
                routes = await self._lookup_online_routes(lookup_batch)

                await self._publish_offline_signal(
                    chat_id=chat.id,
                    ws_event=ws_event,
                    lookup_batch=lookup_batch,
                    routes=routes,
                    message=message,
                    chat=chat
                )

                await self._enqueue_gateway_deliveries(
                    routes,
                    ws_event,
                    message=message,
                    chat=chat,
                    require_subscription=False,
                )

    async def _route_to_active_subscribers(self, chat: ChatDTO, ws_event: WsEvent, message: MessageDTO) -> None:
        async for routes_by_gateway in self._iter_active_subscriber_routes(str(chat.id)):
            await self._enqueue_gateway_deliveries(
                routes_by_gateway,
                ws_event,
                message,
                chat,
                require_subscription=True,
            )

    async def _publish_offline_signal(
        self,
        chat_id: UUID,
        ws_event: WsEvent,
        lookup_batch: Iterable[int],
        routes: RouteMap,
        message: MessageDTO,
        chat: ChatDTO
    ) -> None:
        if ws_event.event_name not in OFFLINE_SIGNAL_EVENT_NAMES:
            return

        online_user_ids: set[int] = set()
        for gateway_users in routes.values():
            online_user_ids |= gateway_users

        offline_user_ids = sorted(set(lookup_batch) - online_user_ids)
        if not offline_user_ids:
            return

        data = {
            "event_id": ws_event.event_id,
            "event_name": ws_event.event_name,
            "payload": {
                "offline_user_ids": offline_user_ids,
                "occurred_at": ws_event.ts,
                "message": message.model_dump(mode="json"),
                "chat": chat.model_dump(mode="json")
            }
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
        message: MessageDTO,
        chat: ChatDTO,
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
                    "type": ws_event.type,
                    "event_id": ws_event.event_id,
                    "event_name": ws_event.event_name,
                    "chat": chat.model_dump(
                        mode="json", exclude_none=True
                    ),
                    "message": message.model_dump(
                        mode="json", exclude_none=True,
                    ),
                    "delivery": {
                        "require_subscription": require_subscription,
                        "recipients": user_chunk,
                        "gateway_id": gateway_id,
                    },
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

