from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.profiles.exceptions import AlreadeExistProfileException
from app.profiles.models.profile import Profile
from app.profiles.repositories.profiles import ProfileRepository


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CreateProfileCommand(BaseCommand):
    user_id: int
    username: str

    display_name: str | None = None
    bio: str | None = None
    skills: set[str] | None = None


@dataclass(frozen=True)
class CreateProfileCommandHanler(BaseCommandHandler[CreateProfileCommand, None]):
    session: AsyncSession
    profile_repository: ProfileRepository

    async def handle(self, command: CreateProfileCommand) -> None:
        profile = await self.profile_repository.get_by_user_id(command.user_id)
        if profile:
            raise AlreadeExistProfileException()

        profile = Profile.create(
            username=command.username,
            user_id=command.user_id,
            display_name=command.display_name,
            bio=command.bio,
            skills=command.skills
        )
        await self.profile_repository.create(profile)
        await self.session.commit()

        logger.info(
            "Profile create", extra={
                "user_id": command.user_id
            }
        )
