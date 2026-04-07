import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.core.services.auth.rbac import RBACManager
from app.projects.exceptions import RoleAlreadyExsistsException
from app.projects.models.role import ProjectRole
from app.projects.repositories.roles import ProjectRoleRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateProjectRoleCommand(BaseCommand):
    name: str
    level: int
    permissions: dict

    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class CreateProjectRoleCommandHandler(BaseCommandHandler[CreateProjectRoleCommand, None]):
    session: AsyncSession
    project_role_repository: ProjectRoleRepository
    rbac_manager: RBACManager

    async def handle(self, command: CreateProjectRoleCommand) -> None:
        if not self.rbac_manager.check_permission(command.user_jwt_data, {"role:create"}):
            raise AccessDeniedException(need_permissions={"role:create" })

        existing = await self.project_role_repository.get_by_name(command.name)
        if existing:
            raise RoleAlreadyExsistsException(role_name=command.name)

        role = ProjectRole.create(
            name=command.name,
            level=command.level,
            permissions=command.permissions
        )

        await self.project_role_repository.create(role)
        await self.session.commit()

        logger.info("Project role created", extra={
            "role": role.name,
            "permissions": command.permissions,
            "created_by": command.user_jwt_data.id
        })
