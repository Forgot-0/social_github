from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.exceptions import NotFoundProjectException
from app.projects.services.permission_service import ProjectPermissionService


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
    project_permission_service: ProjectPermissionService
    event_bus: BaseEventBus

    async def handle(self, command: InviteMemberCommand) -> None:
        project = await self.project_repository.get_by_id(command.project_id, with_member=True)
        if not project:
            raise NotFoundProjectException(project_id=command.project_id)

        role = await self.project_role_repository.get_by_id(command.role_id)
        if not role:
            raise

        if not self.project_permission_service.can_invite(
            user_jwt_data=command.user_jwt_data,
            project=project,
            role=role
        ): raise AccessDeniedException(need_permissions={"memebr:invite", })

        project.invite_memeber(
            user_id=command.user_id,
            role_id=role.id,
            invited_by=int(command.user_jwt_data.id),
            permissions_overrides=command.permissions_overrides
        )

        await self.session.commit()
        await self.event_bus.publish(project.pull_events())
        await self.project_repository.invalidate_cache()

        logger.info("Member invited", extra={
            "project_id": command.project_id,
            "user_id": command.user_id,
            "role_id": command.role_id,
            "permissions_overrides": command.permissions_overrides,
            "invited_by": int(command.user_jwt_data.id),
        })
