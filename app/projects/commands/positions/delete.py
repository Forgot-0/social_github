from dataclasses import dataclass
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.exceptions import NotFoundProjectException
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository
from app.projects.services.permission_service import ProjectPermissionService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeletePositionCommand(BaseCommand):
    position_id: UUID
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class DeletePositionCommandHandler(BaseCommandHandler[DeletePositionCommand, None]):
    session: AsyncSession
    position_repository: PositionRepository
    project_repository: ProjectRepository
    project_permission_service: ProjectPermissionService

    async def handle(self, command: DeletePositionCommand) -> None:
        position = await self.position_repository.get_by_id(str(command.position_id))
        if not position:
            raise NotFoundProjectException(project_id=0)

        project = await self.project_repository.get_by_id(position.project_id, True, False)
        if not project:
            raise NotFoundProjectException(project_id=position.project_id)

        if not self.project_permission_service.can_update(
            user_jwt_data=command.user_jwt_data,
            project=project,
            must_permissions={"position:delete"},
        ):
            raise

        position.soft_delete()
        await self.session.commit()

        await self.position_repository.invadate_cache()
        await self.project_repository.invadate_cache()

        logger.info(
            "Position deleted",
            extra={
                "position_id": str(position.id),
                "project_id": position.project_id,
            },
        )

