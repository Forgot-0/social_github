from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.repositories.projects import ProjectRepository
from app.projects.models.member import MembershipStatus
from app.projects.exceptions import NotFoundProjectException

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateMemberPermissionsCommand(BaseCommand):
    user_jwt_data: UserJWTData
    project_id: int
    target_user_id: int
    permissions_overrides: dict


@dataclass(frozen=True)
class UpdateMemberPermissionsCommandHandler(BaseCommandHandler[UpdateMemberPermissionsCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository

    async def handle(self, command: UpdateMemberPermissionsCommand) -> None:

        logger.info("Member permissions updated", extra={
            "project_id": command.project_id,
            "target_user_id": command.target_user_id,
            "permissions": command.permissions_overrides
        })
