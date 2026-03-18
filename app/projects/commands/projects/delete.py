from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.projects.repositories.projects import ProjectRepository
from app.projects.exceptions import NotFoundProjectException
from app.projects.services.permission_service import ProjectPermissionService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeleteProjectCommand(BaseCommand):
    user_jwt_data: UserJWTData
    project_id: int



@dataclass(frozen=True)
class DeleteProjectCommandHandler(BaseCommandHandler[DeleteProjectCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository
    project_permission_service: ProjectPermissionService
    event_bus: BaseEventBus

    async def handle(self, command: DeleteProjectCommand) -> None:
        project = await self.project_repository.get_by_id(command.project_id, with_member=True)
        if not project:
            raise NotFoundProjectException(project_id=command.project_id)

        if not self.project_permission_service.can_update(
            user_jwt_data=command.user_jwt_data,
            project=project,
            must_permissions={"project:delete",}
        ): raise AccessDeniedException(need_permissions={"project:delete", })

        project.soft_delete()
        await self.session.commit()
        await self.event_bus.publish(project.pull_events())

        await self.project_repository.invadate_cache()
        logger.info(
            "Project deleted",
            extra={"project_id": project.id, "deleted_by": command.user_jwt_data.id}
        )
