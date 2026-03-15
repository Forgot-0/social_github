import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.commands.projects.create import CreateProjectCommand, CreateProjectCommandHandler
from app.projects.config import project_config
from app.projects.exceptions import AlreadySlugProjectExistsException, MaxProjectsLimitExceededException
from app.projects.repositories.projects import ProjectRepository
from tests.projects.integration.factories import ProjectCommandFactory


@pytest.mark.integration
@pytest.mark.projects
class TestCreateProjectCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        project_repository: ProjectRepository,
    ) -> CreateProjectCommandHandler:
        return CreateProjectCommandHandler(
            session=db_session,
            project_repository=project_repository,
        )

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        project_repository: ProjectRepository,
        handler
    ) -> None:

        cmd_data = ProjectCommandFactory.create_command(
            owner_id=1,
            name="Test project",
            slug="test-project",
            small_description="short",
            description="long",
        )
        command = CreateProjectCommand(**cmd_data)

        await handler.handle(command)

        created = await project_repository.get_by_slug("test-project")
        assert created is not None
        assert created.owner_id == 1

    @pytest.mark.asyncio
    async def test_limit_projects_per_user(
        self,
        handler
    ) -> None:

        for i in range(project_config.MAX_PROJECTS_PER_USER):
            cmd_data = ProjectCommandFactory.create_command(
                owner_id=1,
                name=f"Project {i}",
                slug=f"project-{i}",
            )
            command = CreateProjectCommand(**cmd_data)
            await handler.handle(command)

        cmd_data = ProjectCommandFactory.create_command(
            owner_id=1,
            name="Overflow project",
            slug="overflow-project",
        )
        command = CreateProjectCommand(**cmd_data)

        with pytest.raises(MaxProjectsLimitExceededException):
            await handler.handle(command)


    @pytest.mark.asyncio
    async def test_already_slug_exists(self, handler) -> None:
        cmd_data = ProjectCommandFactory.create_command(
            owner_id=1,
            name="Overflow project",
            slug="overflow-project",
        )
        command = CreateProjectCommand(**cmd_data)
        await handler.handle(command)

        with pytest.raises(AlreadySlugProjectExistsException):
            await handler.handle(command)
