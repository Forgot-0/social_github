import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.projects.exceptions import AlreadyMemberException, NotFoundProjectException
from app.projects.models.role_permissions import ProjectRolesEnum
from app.projects.repositories.applications import ApplicationRepository
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository
from app.projects.services.permission_service import ProjectPermissionService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DecideApplicationCommand(BaseCommand):
    application_id: UUID
    approve: bool
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class DecideApplicationCommandHandler(BaseCommandHandler[DecideApplicationCommand, None]):
    session: AsyncSession
    application_repository: ApplicationRepository
    project_repository: ProjectRepository
    position_repository: PositionRepository
    project_permission_service: ProjectPermissionService

    async def handle(self, command: DecideApplicationCommand) -> None:
        application = await self.application_repository.get_by_id(command.application_id, with_position=True)
        if not application:
            raise NotFoundProjectException(project_id=0)

        project = await self.project_repository.get_by_id(
            application.project_id,
            with_member=True, with_positon=True
        )
        if not project:
            raise NotFoundProjectException(project_id=application.project_id)

        if not self.project_permission_service.can_update(
            user_jwt_data=command.user_jwt_data,
            project=project,
            must_permissions={"member:invite"},
        ):
            raise AccessDeniedException(need_permissions={"member:invite"})

        if command.approve:
            application.accept(decided_by=int(command.user_jwt_data.id))

            existing_member = project.get_memeber_by_user_id(application.candidate_id)
            if existing_member is not None:
                raise AlreadyMemberException()

            project.invite_memeber(
                user_id=application.candidate_id,
                role_id=ProjectRolesEnum.USER.value.id,
                invited_by=int(command.user_jwt_data.id),
            )

            membership = project.get_memeber_by_user_id(application.candidate_id)
            if membership:
                membership.accept_invite()

        else:
            application.reject(decided_by=int(command.user_jwt_data.id))

        await self.session.commit()

        await self.project_repository.invalidate_cache()
        await self.application_repository.invalidate_cache()

        logger.info(
            "Application decided",
            extra={
                "application_id": str(application.id),
                "project_id": application.project_id,
                "position_id": str(application.position_id),
                "approved": command.approve,
                "decided_by": command.user_jwt_data.id,
            },
        )

