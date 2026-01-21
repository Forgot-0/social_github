from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.event import BaseEvent, BaseEventHandler
from app.profiles.repositories.profiles import ProfileRepository


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadedAvatarsEvent(BaseEvent):
    user_id: int
    versions: dict[str, dict[str, str]]



@dataclass(frozen=True)
class UploadedAvatarsEventHandler(BaseEventHandler[UploadedAvatarsEvent, None]):
    session: AsyncSession
    profile_repository: ProfileRepository

    async def __call__(self, event: UploadedAvatarsEvent) -> None:
        profile = await self.profile_repository.get_by_user_id(event.user_id)
        if profile is None:
            raise

        profile.avatars = event.versions
        await self.session.commit()
        logger.info(
            "Avatars resize complated", extra={
                "user_id": event.user_id, "avatars": event.versions
            }
        )
