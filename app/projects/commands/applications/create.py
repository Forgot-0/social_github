from dataclasses import dataclass
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.exceptions import NotFoundPositionException, NotFoundProjectException
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
        position = await self.position_repository.get_by_id(str(command.position_id), with_project=True)
        if not position:
            raise NotFoundPositionException(position_id=str(command.position_id))

        position.add_application(
            candidate_id=int(command.user_jwt_data.id),
            message=command.message
        )

        await self.session.commit()
        await self.project_repository.invalidate_cache()
        await self.application_repository.invalidate_cache()

        logger.info(
            "Application created",
            extra={
                "position_id": str(position.id),
                "project_id": position.project.id,
                "candidate_id": command.user_jwt_data.id,
            },
        )

