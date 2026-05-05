from __future__ import annotations

from typing import Any

from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaRouter

from app.chats.config import chat_config
from app.chats.services.delivery_router import ChatDeliveryRouter

router = KafkaRouter()


@router.subscriber(
    chat_config.CHAT_TOPIC,
    group_id=chat_config.DELIVERY_ROUTER_GROUP_ID,
)
@inject
async def route_chat_delivery_event(
    event: dict[str, Any],
    delivery_router: FromDishka[ChatDeliveryRouter],
) -> None:
    await delivery_router.route_broker_message(event)
