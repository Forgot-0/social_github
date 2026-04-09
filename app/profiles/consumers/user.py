from dishka.integrations.faststream import FromDishka
from faststream.kafka import KafkaRouter

from app.core.configs.app import app_config
from app.core.mediators.base import BaseMediator
from app.profiles.commands.profiles.create import CreateProfileCommand
from app.profiles.config import profile_config

router = KafkaRouter()

@router.subscriber(profile_config.USER_TOPIC, group_id=app_config.GROUP_ID)
async def create_profile(msg: dict, mediator: FromDishka[BaseMediator]):
    user_id = msg.get("user_id")
    username = msg.get("username")
    if user_id is None or username is None:
        return

    await mediator.handle_command(
        CreateProfileCommand(user_id=int(user_id), username=username)
    )
