from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.event import BaseEvent, BaseEventHandler
from app.core.services.storage.service import StorageService
from app.profiles.config import profile_config
from app.profiles.exceptions import NotFoundProfileException
from app.profiles.repositories.profiles import ProfileRepository


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadedAvatarsEvent(BaseEvent):
    user_id: int
    versions: dict[int, dict[str, str]]


@dataclass(frozen=True)
class UploadedAvatarsEventHandler(BaseEventHandler[UploadedAvatarsEvent, None]):
    session: AsyncSession
    profile_repository: ProfileRepository
    storage_service: StorageService

    async def __call__(self, event: UploadedAvatarsEvent) -> None:
        profile = await self.profile_repository.get_by_user_id(event.user_id)
        if profile is None:
            raise NotFoundProfileException(profile_id=event.user_id)

        for version in profile.avatars:
            for key in profile.avatars[version]:
                await self.storage_service.delete_file(
                    profile_config.AVATAR_BUCKET,
                    profile.avatars[version][key].split(profile_config.AVATAR_BUCKET)[-1]
                )

        profile.avatars = event.versions # type: ignore
        await self.session.commit()
        logger.info(
            "Avatars resize complated", extra={
                "user_id": event.user_id, "avatars": event.versions
            }
        )
