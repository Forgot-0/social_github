from dataclasses import dataclass
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.exceptions import NotFoundProjectException
from app.projects.models.application import Application
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.applications import ApplicationRepository


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateApplicationCommand(BaseCommand):
    position_id: UUID
    message: str | None
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class CreateApplicationCommandHandler(BaseCommandHandler[CreateApplicationCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository
    position_repository: PositionRepository
    application_repository: ApplicationRepository

    async def handle(self, command: CreateApplicationCommand) -> None:
        position = await self.position_repository.get_by_id(str(command.position_id))
        if not position:
            raise NotFoundProjectException(project_id=0)

        project = await self.project_repository.get_by_id(position.project_id)
        if not project:
            raise NotFoundProjectException(project_id=position.project_id)

        application = Application.create(
            project_id=project.id,
            position_id=position.id,
            candidate_id=int(command.user_jwt_data.id),
            message=command.message,
        )

        await self.application_repository.create(application)
        await self.session.commit()

        logger.info(
            "Application created",
            extra={
                "application_id": str(application.id),
                "position_id": str(position.id),
                "project_id": project.id,
                "candidate_id": command.user_jwt_data.id,
            },
        )

