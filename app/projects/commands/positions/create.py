from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.projects.exceptions import NotFoundProjectException
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.services.permission_service import ProjectPermissionService
from app.projects.models.position import PositionLocationType, PositionLoad


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CreatePositionCommand(BaseCommand):
    user_jwt_data: UserJWTData

    project_id: int
    title: str
    description: str
    required_skills: set[str]

    responsibilities: str | None = None
    location_type: str | None = None
    expected_load: str | None = None




@dataclass(frozen=True)
class CreatePositionCommandHandler(BaseCommandHandler[CreatePositionCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository
    project_role_repository: ProjectRoleRepository
    project_permission_service: ProjectPermissionService
    event_bus: BaseEventBus

    async def handle(self, command: CreatePositionCommand) -> None:
        project = await self.project_repository.get_by_id(command.project_id, True, True)

        if not project:
            raise NotFoundProjectException(project_id=command.project_id)

        if not self.project_permission_service.can_update(
            user_jwt_data=command.user_jwt_data,
            project=project,
            must_permissions={"position:create", }
        ): raise AccessDeniedException(need_permissions={"position:create", })

        project.new_position(
            title=command.title,
            description=command.description,
            required_skills=command.required_skills,
            responsibilities=command.responsibilities,
            location_type=command.location_type,
            expected_load=command.expected_load,
        )
        await self.session.commit()

        await self.event_bus.publish(project.pull_events())

        logger.info(
            "Create new position", extra={
                "created_by": command.user_jwt_data.id,
                "project)id": command.project_id,
                "title": command.title,
            }
        )
