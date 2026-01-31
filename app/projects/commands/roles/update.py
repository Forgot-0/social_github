from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.exceptions import NotFoundRoleException

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateProjectRoleCommand(BaseCommand):
    role_id: int
    permissions: dict

    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class UpdateProjectRoleCommandHandler(BaseCommandHandler[UpdateProjectRoleCommand, None]):
    session: AsyncSession
    project_role_repository: ProjectRoleRepository
    rbac_manager: RBACManager

    async def handle(self, command: UpdateProjectRoleCommand) -> None:
        if not self.rbac_manager.check_permission(command.user_jwt_data, {"role:update"}):
            raise 

        role = await self.project_role_repository.get_by_id(command.role_id)
        if not role:
            raise NotFoundRoleException(role_id=command.role_id)

        role.permissions = command.permissions
        await self.session.commit()

        logger.info("Project role updated", extra={"role_id": role.id})
