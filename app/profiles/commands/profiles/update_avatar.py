from dataclasses import dataclass
import logging

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.queues.service import QueueService
from app.profiles.repositories.profiles import ProfileRepository
from app.profiles.tasks import AvatarUploadTask


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class UpdateProfileAvatrCommand(BaseCommand):
    key_base: str
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class UpdateProfileAvatrCommandHandler(BaseCommandHandler[UpdateProfileAvatrCommand, None]):
    queue_service: QueueService
    profile_repository: ProfileRepository

    async def handle(self, command: UpdateProfileAvatrCommand) -> None:
        await self.queue_service.push(
            AvatarUploadTask, {
                "user_id": int(command.user_jwt_data.id),
                "key_base": command.key_base
            }
        )
        await self.profile_repository.invalidate_cache()

        logger.info(
            "Start proccess avatar resize", extra={
                "key_base": command.key_base, "user_id": command.user_jwt_data.id
            }
        )
