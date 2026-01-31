from dataclasses import dataclass
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.models.member import ProjectMembership, MembershipStatus
from app.projects.exceptions import NotFoundProjectException


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InviteMemberCommand(BaseCommand):
    user_jwt_data: UserJWTData

    project_id: int
    user_id: int
    role_id: int
    permissions_overrides: dict | None = None


@dataclass(frozen=True)
class InviteMemberCommandHandler(BaseCommandHandler[InviteMemberCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository
    project_role_repository: ProjectRoleRepository

    async def handle(self, command: InviteMemberCommand) -> None:
        project = await self.project_repository.get_by_id(command.project_id)
        if not project:
            raise NotFoundProjectException(project_id=command.project_id)

        role = await self.project_role_repository.get_by_id(command.role_id)
        if not role:
            raise

        project.invite_memeber(
            user_id=command.user_id,
            role_id=role.id,
            invited_by=int(command.user_jwt_data.id),
            permissions_overrides=command.permissions_overrides
        )

        await self.session.commit()

        logger.info("Member invited", extra={
            "project_id": command.project_id,
            "user_id": command.user_id,
            "role_id": command.role_id,
            "permissions_overrides": command.permissions_overrides,
            "invited_by": int(command.user_jwt_data.id),
        })
