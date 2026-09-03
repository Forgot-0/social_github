import asyncio
import contextlib
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from uuid import UUID

from redis.asyncio import Redis

from app.chats.config import chat_config
from app.chats.dtos.chats import ChatDTO
from app.chats.dtos.delivery import (
    CHAT_EVENT_TO_WS_TYPE,
    REACTION_EVENT_NAME,
    MessagePayloadWS,
    WsEvent,
    build_reaction_ws_dto,
    chunks,
)
from app.chats.dtos.messages import MessageDTO
from app.chats.dtos.reactions import ReactionUpdateWSDTO
from app.chats.metrics import (
    CHAT_REACTION_FANOUT_TOTAL,
    DELIVERY_ROUTER_OFFLINE_RECIPIENTS,
    DELIVERY_ROUTER_OFFLINE_SIGNALS,
    DELIVERY_ROUTER_STREAM_ENTRIES,
)
from app.chats.models.chat import ChatFanoutStrategy
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.schemas.ws import ChatEventPayload
from app.chats.services.messages import MessageService
from app.core.configs.app import app_config
from app.core.consumers.event import TypedEventDTO
from app.core.message_brokers.base import BaseMessageBroker
from app.core.utils import now_utc
from app.core.websocket.dtos import DeliveryData, DeliveryDTO
from app.core.websocket.keys import WebsocketKeys

RouteMap = dict[str, set[int]]
ActiveSubscriptionRoute = tuple[int, str, str, str]

OFFLINE_SIGNAL_EVENT_NAMES: frozenset[str] = frozenset({"chats.message.sent"})


@dataclass
class ChatDeliveryRouter:
    redis: Redis
    chat_repository: ChatRepository
    message_repository: MessageRepository
    message_service: MessageService
    broker: BaseMessageBroker

    async def route_broker_message(self, event: TypedEventDTO[ChatEventPayload]) -> None:

        chat = await self.chat_repository.get_by_id(event.payload.chat_id)
        if chat is None:
            return

        ws_event = WsEvent.build(event, fanout_strategy=chat.fanout_strategy)

        if event.event_name == REACTION_EVENT_NAME:
            reaction = build_reaction_ws_dto(event.payload)
            CHAT_REACTION_FANOUT_TOTAL.labels(mode="immediate").inc()
            await self._dispatch(
                ChatDTO.model_validate(chat), ws_event, reaction=reaction
            )
            return

        message_dto: MessageDTO | None = None
        if event.payload.message_id:
            message = await self.message_repository.get_by_id(event.payload.message_id, for_offline=True)
            if message is None:
                return

            message_dto = MessageDTO.model_validate(message)
            await self.message_service.attach_profile_urls([message_dto.profile])

        await self._dispatch(
            ChatDTO.model_validate(chat), ws_event, message=message_dto
        )

    async def route_reaction_snapshot(self, payload: dict) -> None:
        chat = await self.chat_repository.get_by_id(UUID(str(payload["chat_id"])))
        if chat is None:
            return

        ws_event = WsEvent(
            type=CHAT_EVENT_TO_WS_TYPE[REACTION_EVENT_NAME],
            event_name=REACTION_EVENT_NAME,
            event_id=str(payload.get("event_id", "")),
            chat_id=chat.id,
            payload=ChatEventPayload(
                chat_id=chat.id, message_id=UUID(str(payload["message_id"]))
            ),
            ts=str(payload.get("ts") or now_utc().isoformat()),
            fanout_strategy=chat.fanout_strategy,
        )

        CHAT_REACTION_FANOUT_TOTAL.labels(mode="coalesced").inc()
        await self._dispatch(
            ChatDTO.model_validate(chat),
            ws_event,
            reaction=build_reaction_ws_dto(payload),
        )

    async def _dispatch(
        self,
        chat: ChatDTO,
        ws_event: WsEvent,
        *,
        message: MessageDTO | None = None,
        reaction: ReactionUpdateWSDTO | None = None,
    ) -> None:
        if ws_event.fanout_strategy == ChatFanoutStrategy.FANOUT_ON_WRITE:
            await self._route_fanout_on_write(
                chat=chat, ws_event=ws_event, message=message, reaction=reaction
            )
            return

        await self._route_to_active_subscribers(
            chat=chat, ws_event=ws_event, message=message, reaction=reaction
        )

    async def _route_fanout_on_write(
        self,
        chat: ChatDTO,
        ws_event: WsEvent,
        message: MessageDTO | None=None,
        reaction: ReactionUpdateWSDTO | None = None,
    ) -> None:
        async for member_ids in self.chat_repository.iter_member_ids(
            chat_id=chat.id,
            batch_size=chat_config.DELIVERY_ROUTER_MEMBER_BATCH_SIZE,
        ):
            for lookup_batch in chunks(member_ids, chat_config.DELIVERY_ROUTER_ROUTE_LOOKUP_BATCH_SIZE):
                routes = await self._lookup_online_routes(lookup_batch)

                await self._publish_offline_signal(
                    ws_event=ws_event,
                    lookup_batch=lookup_batch,
                    routes=routes,
                    chat=chat,
                    message=message,
                )

                await self._enqueue_gateway_deliveries(
                    routes,
                    ws_event,
                    require_subscription=False,
                    message=message,
                    reaction=reaction,
                )

    async def _route_to_active_subscribers(
        self,
        chat: ChatDTO,
        ws_event: WsEvent,
        message: MessageDTO | None=None,
        reaction: ReactionUpdateWSDTO | None = None,
    ) -> None:
        async for routes_by_gateway in self._iter_active_subscriber_routes(str(chat.id)):
            await self._enqueue_gateway_deliveries(
                routes_by_gateway,
                ws_event,
                require_subscription=True,
                message=message,
                reaction=reaction,
            )

    async def _publish_offline_signal(
        self,
        ws_event: WsEvent,
        lookup_batch: Iterable[int],
        routes: RouteMap,
        chat: ChatDTO,
        message: MessageDTO | None=None,
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
                "message": message.model_dump(mode="json") if message else None,
                "chat": chat.model_dump(mode="json"),
            },
        }

        await self.broker.send_data(
            key=str(ws_event.chat_id),
            topic=chat_config.CHAT_OFFLINE_DELIVERY_TOPIC,
            data=data,
        )

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
                self.redis.srem(subscription_key, *stale),  # pyright: ignore[reportArgumentType]
                name="ws:sub:cleanup:stale",
            )

        return routes_by_gateway

    async def _enqueue_gateway_deliveries(
        self,
        routes_by_gateway: RouteMap,
        ws_event: WsEvent,
        *,
        require_subscription: bool,
        message: MessageDTO | None=None,
        reaction: ReactionUpdateWSDTO | None = None,
    ) -> None:
        if not routes_by_gateway:
            return

        payload = MessagePayloadWS(message=message, reaction=reaction).model_dump(mode="json")

        pipe = self.redis.pipeline(transaction=False)
        enqueued = 0

        for gateway_id, user_ids in routes_by_gateway.items():
            stream_key = WebsocketKeys.gateway_stream_key(gateway_id)
            for user_chunk in chunks(sorted(user_ids), app_config.WS_GATEWAY_STREAM_USERS_PER_ENTRY):
                stream_event = DeliveryDTO(
                    type=ws_event.type,
                    payload=payload,
                    delivery=DeliveryData(
                        require_subscription=require_subscription, recipients=user_chunk
                    ),
                    ts=ws_event.ts,
                    channel=str(ws_event.chat_id)
                )
                pipe.xadd(
                    stream_key,
                    fields={"event": stream_event.model_dump_json()},
                    maxlen=app_config.WS_GATEWAY_STREAM_MAXLEN,
                    approximate=True,
                )
                enqueued += 1

        if not enqueued:
            return

        await pipe.execute()
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
