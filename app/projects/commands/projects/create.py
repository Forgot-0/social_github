from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.projects.config import project_config
from app.projects.exceptions import MaxProjectsLimitExceededException
from app.projects.models.project import Project, ProjectVisibility
from app.projects.repositories.projects import ProjectRepository


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateProjectCommand(BaseCommand):
    owner_id: int
    name: str
    slug: str
    small_description: str | None = None
    description: str | None = None
    visibility: str | None = None
    meta_data: dict | None = None
    tags: set[str] | None = None


@dataclass(frozen=True)
class CreateProjectCommandHandler(BaseCommandHandler[CreateProjectCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository

    async def handle(self, command: CreateProjectCommand) -> None:
        existing = await self.project_repository.get_by_name(command.name)
        if existing:
            raise

        projects_count = await self.project_repository.count_by_owner(command.owner_id)
        if projects_count >= project_config.MAX_PROJECTS_PER_USER:
            raise MaxProjectsLimitExceededException(
                owner_id=command.owner_id,
                limit=project_config.MAX_PROJECTS_PER_USER,
            )

        project = Project.create(
            owner_id=command.owner_id,
            name=command.name,
            slug=command.slug,
            small_description=command.small_description or "",
            full_description=command.description or "",
            visibility=ProjectVisibility(command.visibility) if command.visibility else ProjectVisibility.public,
            metadata=command.meta_data or {},
            tags=command.tags or set(),
        )

        await self.project_repository.create(project)
        await self.session.commit()

        logger.info("Project created", extra={"project": project.name, "owner": command.owner_id})
