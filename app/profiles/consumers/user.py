import logging

from dishka.integrations.faststream import FromDishka
from faststream.kafka import KafkaRouter

from app.core.configs.app import app_config
from app.core.consumers.idempotency import EventIdempotencyGuard, extract_event_id
from app.core.mediators.base import BaseMediator
from app.profiles.commands.profiles.create import CreateProfileCommand
from app.profiles.config import profile_config

logger = logging.getLogger(__name__)

router = KafkaRouter()



@router.subscriber(profile_config.USER_TOPIC, group_id=app_config.GROUP_ID)
async def create_profile(
    msg: dict,
    mediator: FromDishka[BaseMediator],
    idempotency_guard: FromDishka[EventIdempotencyGuard],
) -> None:
    user_id = msg.get("user_id")
    username = msg.get("username")
    if user_id is None or username is None:
        return

    event_id = extract_event_id(msg)
    if event_id is not None and not await idempotency_guard.try_acquire(
        group=f"{app_config.GROUP_ID}:create_profile", event_id=event_id
    ):
        return

    try:
        await mediator.handle_command(
            CreateProfileCommand(user_id=int(user_id), username=username)
        )
    except Exception:
        if event_id is not None:
            await idempotency_guard.release(
                group=f"{app_config.GROUP_ID}:create_profile", event_id=event_id
            )
        raise
