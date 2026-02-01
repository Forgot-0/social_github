from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.projects.repositories.projects import ProjectRepository
from app.projects.exceptions import NotFoundProjectException
from app.projects.services.permission_service import ProjectPermissionService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateProjectCommand(BaseCommand):
    user_jwt_data: UserJWTData
    project_id: int

    name: str | None = None
    description: str | None = None
    visibility: str | None = None
    meta_data: dict | None = None
    tags: set[str] | None = None



@dataclass(frozen=True)
class UpdateProjectCommandHandler(BaseCommandHandler[UpdateProjectCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository
    project_permission_service: ProjectPermissionService
    event_bus: BaseEventBus

    async def handle(self, command: UpdateProjectCommand) -> None:
        project = await self.project_repository.get_by_id(command.project_id)
        if not project:
            raise NotFoundProjectException(project_id=command.project_id)

        if not self.project_permission_service.can_update(
            user_jwt_data=command.user_jwt_data,
            project=project,
            must_permissions={"project:update",}
        ): raise 

        if command.name is not None:
            project.update_name(command.name)
        if command.description is not None:
            project.update_description(command.description)
        if command.visibility is not None:
            project.update_visibility(command.visibility)
        if command.tags is not None:
            project.update_tags(command.tags)

        await self.session.commit()
        await self.event_bus.publish(project.pull_events())

        logger.info("Project updated", extra={"project_id": project.id})
