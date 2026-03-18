from dataclasses import dataclass
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.projects.exceptions import NotFoundProjectException
from app.projects.models.position import PositionLocationType, PositionLoad
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository
from app.projects.services.permission_service import ProjectPermissionService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdatePositionCommand(BaseCommand):
    position_id: UUID
    user_jwt_data: UserJWTData

    title: str | None = None
    description: str | None = None
    responsibilities: str | None = None
    required_skills: set[str] | None = None
    location_type: str | None = None
    expected_load: str | None = None


@dataclass(frozen=True)
class UpdatePositionCommandHandler(BaseCommandHandler[UpdatePositionCommand, None]):
    session: AsyncSession
    position_repository: PositionRepository
    project_repository: ProjectRepository
    project_permission_service: ProjectPermissionService
    event_bus: BaseEventBus

    async def handle(self, command: UpdatePositionCommand) -> None:
        position = await self.position_repository.get_by_id(str(command.position_id))
        if not position:
            raise NotFoundProjectException(project_id=0)

        project = await self.project_repository.get_by_id(position.project_id, True, False)
        if not project:
            raise NotFoundProjectException(project_id=position.project_id)

        if not self.project_permission_service.can_update(
            user_jwt_data=command.user_jwt_data,
            project=project,
            must_permissions={"position:update"},
        ):
            raise

        if command.title is not None:
            position.title = command.title
        if command.description is not None:
            position.description = command.description
        if command.responsibilities is not None:
            position.responsibilities = command.responsibilities
        if command.required_skills is not None:
            position.required_skills = list(command.required_skills)
        if command.location_type is not None:
            position.location_type = PositionLocationType(command.location_type)
        if command.expected_load is not None:
            position.expected_load = PositionLoad(command.expected_load)

        await self.session.commit()
        await self.event_bus.publish(project.pull_events())

        await self.position_repository.invadate_cache()
        await self.project_repository.invadate_cache()

        logger.info(
            "Position updated",
            extra={
                "position_id": str(position.id),
                "project_id": position.project_id,
            },
        )

