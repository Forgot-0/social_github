from typing import Any

from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaRouter

from app.chats.commands.profiles.upsert import UpsertProfileProjectionCommand
from app.chats.config import chat_config
from app.core.mediators.base import BaseMediator


router = KafkaRouter()


@router.subscriber(
    chat_config.PROFILE_TOPIC,
    group_id=chat_config.DELIVERY_ROUTER_GROUP_ID,
)
@inject
async def route_profile_delivery_event(
    event: dict[str, Any],
    mediator: FromDishka[BaseMediator],
) -> None:
    user_id = int(event["user_id"])
    username = str(event["username"])

    await mediator.handle_command(
        UpsertProfileProjectionCommand(
            user_id=user_id,
            username=username,
            display_name=event.get("display_name"),
            avatars=event.get("avatars", {})
        )
    )
