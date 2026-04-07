import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.event import BaseEvent, BaseEventHandler
from app.profiles.exceptions import NotFoundProfileException
from app.profiles.repositories.profiles import ProfileRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadedAvatarsEvent(BaseEvent):
    profile_id: int
    versions: dict[int, dict[str, str]]


@dataclass(frozen=True)
class UploadedAvatarsEventHandler(BaseEventHandler[UploadedAvatarsEvent, None]):
    session: AsyncSession
    profile_repository: ProfileRepository

    async def __call__(self, event: UploadedAvatarsEvent) -> None:
        profile = await self.profile_repository.get_by_id(event.profile_id)
        if profile is None:
            raise NotFoundProfileException(profile_id=event.profile_id)

        profile.avatars = event.versions # type: ignore
        await self.session.commit()
        await self.profile_repository.invalidate_cache()

        logger.info(
            "Avatars resize complated", extra={
                "user_id": event.profile_id,
            }
        )
