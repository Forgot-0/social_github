import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedError
from app.projects.exceptions import NotFoundMemberError, NotFoundProjectError, NotFoundProjectRoleError
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.services.permission_service import ProjectPermissionService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChangeRoleMemberCommand(BaseCommand):
    user_jwt_data: UserJWTData
    project_id: int
    target_user_id: int
    role_id: int


@dataclass(frozen=True)
class ChangeRoleMemberCommandHandler(BaseCommandHandler[ChangeRoleMemberCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository
    role_repository: ProjectRoleRepository
    project_permission_servise: ProjectPermissionService

    async def handle(self, command: ChangeRoleMemberCommand) -> None:
        project = await self.project_repository.get_by_id(command.project_id, with_member=True)
        if project is None:
            raise NotFoundProjectError(project_id=command.project_id)

        if not self.project_permission_servise.can_update(
            user_jwt_data=command.user_jwt_data,
            project=project,
            must_permissions={"member:update", "permission:update"}
        ):
            raise AccessDeniedError(need_permissions={"member:update", "permission:update"})

        member = project.get_memeber_by_user_id(command.target_user_id)
        if member is None:
            raise NotFoundMemberError(member_id=command.target_user_id)

        role = await self.role_repository.get_by_id(command.role_id)
        if role is None:
            raise NotFoundProjectRoleError(role_id=command.role_id)

        member.role_id = role.id
        await self.session.commit()
        await self.project_repository.invalidate_cache()

        logger.info("Member change role", extra={
            "project_id": command.project_id,
            "target_user_id": command.target_user_id,
            "role_id": command.role_id
        })
