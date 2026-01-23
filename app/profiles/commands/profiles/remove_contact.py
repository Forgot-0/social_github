from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import AccessDeniedException
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.profiles.exceptions import NotFoundProfileException
from app.profiles.repositories.profiles import ProfileRepository


@dataclass(frozen=True)
class RemoveContactToProfileCommand(BaseCommand):
    profile_id: int
    provider: str

    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class RemoveContactToProfileCommandHandler(BaseCommandHandler[RemoveContactToProfileCommand, None]):
    session: AsyncSession
    profile_repository: ProfileRepository
    rbac_manager: RBACManager

    async def handle(self, command: RemoveContactToProfileCommand) -> None:
        profile = await self.profile_repository.get_by_id(command.profile_id)

        if profile is None:
            raise NotFoundProfileException(profile_id=command.profile_id)

        if (
            profile.user_id != int(command.user_jwt_data.id) and
            not self.rbac_manager.check_permission(command.user_jwt_data, {"profile:update", "user:update" })
        ):
            raise AccessDeniedException(
                need_permissions={"profile:update", "user:update" } - set(command.user_jwt_data.permissions)
            )

        profile.remove_contact(command.provider)
        await self.session.commit()

