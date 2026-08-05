import logging
from typing import Any

from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaRouter

from app.chats.config import chat_config
from app.chats.services.delivery_router import ChatDeliveryRouter
from app.core.consumers.idempotency import EventIdempotencyGuard, extract_event_id

logger = logging.getLogger(__name__)

router = KafkaRouter()


@router.subscriber(
    chat_config.CHAT_TOPIC,
    group_id=chat_config.DELIVERY_ROUTER_GROUP_ID,
)
@inject
async def route_chat_delivery_event(
    event: dict[str, Any],
    delivery_router: FromDishka[ChatDeliveryRouter],
    idempotency_guard: FromDishka[EventIdempotencyGuard],
) -> None:
    event_id = extract_event_id(event)
    if event_id is not None and not await idempotency_guard.try_acquire(
        group=chat_config.DELIVERY_ROUTER_GROUP_ID, event_id=event_id
    ):
        return

    try:
        await delivery_router.route_broker_message(event)
    except Exception:
        if event_id is not None:
            await idempotency_guard.release(
                group=chat_config.DELIVERY_ROUTER_GROUP_ID, event_id=event_id
            )
        raise
