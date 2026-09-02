import logging

from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaRouter

from app.chats.config import chat_config
from app.chats.dtos.delivery import REACTION_EVENT_NAME
from app.chats.schemas.ws import ChatEventPayload
from app.chats.services.delivery_router import ChatDeliveryRouter
from app.chats.services.reaction_coalescer import (
    ReactionCoalesceQueue,
    reaction_ws_payload_from_event,
)
from app.core.consumers.event import TypedEventDTO
from app.core.consumers.idempotency import EventIdempotencyGuard

logger = logging.getLogger(__name__)

router = KafkaRouter()


@router.subscriber(
    chat_config.CHAT_TOPIC,
    group_id=chat_config.DELIVERY_ROUTER_GROUP_ID,
)
@inject
async def route_chat_delivery_event(
    event: TypedEventDTO[ChatEventPayload],
    delivery_router: FromDishka[ChatDeliveryRouter],
    coalesce_queue: FromDishka[ReactionCoalesceQueue],
    idempotency_guard: FromDishka[EventIdempotencyGuard],
) -> None:
    if not await idempotency_guard.try_acquire(
        group=chat_config.DELIVERY_ROUTER_GROUP_ID, event_id=event.event_id
    ):
        return

    try:
        if (
            event.event_name == REACTION_EVENT_NAME
            and chat_config.REACTIONS_COALESCE_ENABLED
        ):
            payload = reaction_ws_payload_from_event(event.payload)
            payload["event_id"] = str(event.event_id)
            payload["ts"] = event.created_at.isoformat()
            await coalesce_queue.enqueue(payload)
            return

        await delivery_router.route_broker_message(event)
    except Exception:
        await idempotency_guard.release(
            group=chat_config.DELIVERY_ROUTER_GROUP_ID, event_id=event.event_id
        )
        raise
