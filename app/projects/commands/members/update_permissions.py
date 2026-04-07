import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.projects.exceptions import NotFoundMemberException, NotFoundProjectException
from app.projects.repositories.projects import ProjectRepository
from app.projects.services.permission_service import ProjectPermissionService

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
    project_permission_servise: ProjectPermissionService

    async def handle(self, command: UpdateMemberPermissionsCommand) -> None:
        project = await self.project_repository.get_by_id(command.project_id, with_member=True)
        if not project:
            raise NotFoundProjectException(project_id=command.project_id)

        if not self.project_permission_servise.can_update(
            user_jwt_data=command.user_jwt_data,
            project=project,
            must_permissions={"member:update", "permission:update"}
        ): raise AccessDeniedException(need_permissions={"member:update", "permission:update"})

        member = project.get_memeber_by_user_id(command.target_user_id)
        if member is None:
            raise NotFoundMemberException(memebr_id=command.target_user_id)

        member.permissions_overrides = command.permissions_overrides
        await self.session.commit()

        logger.info("Member permissions updated", extra={
            "project_id": command.project_id,
            "target_user_id": command.target_user_id,
            "permissions": command.permissions_overrides
        })
