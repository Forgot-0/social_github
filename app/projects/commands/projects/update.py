from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.models.project import ProjectVisibility
from app.projects.repositories.projects import ProjectRepository
from app.projects.exceptions import NotFoundProjectException


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

    async def handle(self, command: UpdateProjectCommand) -> None:
        project = await self.project_repository.get_by_id(command.project_id)
        if not project:
            raise NotFoundProjectException(project_id=command.project_id)

        user_id = int(command.user_jwt_data.id)
        if project.owner_id != user_id:
            member = await self.project_repository.get_membership(command.project_id, user_id)
            if member is None:
                raise Exception("No permission to update project")
            perms = member.effective_permissions()
            if not perms.get("update_project", False):
                raise Exception("No permission to update project")

        if command.name is not None:
            project.update_name(command.name)
        if command.description is not None:
            project.description = command.description
        if command.visibility is not None:
            project.visibility = ProjectVisibility(command.visibility)
        if command.meta_data is not None:
            project.meta_data = command.meta_data
        if command.tags is not None:
            project.update_tags(command.tags)

        await self.session.commit()

        logger.info("Project updated", extra={"project_id": project.id})
