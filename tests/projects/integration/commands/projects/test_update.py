import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.commands.projects.update import UpdateProjectCommandHandler
from app.projects.repositories.projects import ProjectRepository
from app.projects.services.permission_service import ProjectPermissionService



@pytest.mark.integration
@pytest.mark.projects
class TestUpdateProjectCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        project_repository: ProjectRepository,
        project_permission_service: ProjectPermissionService,
        mock_event_bus
    ) -> UpdateProjectCommandHandler:
        return UpdateProjectCommandHandler(
            session=db_session,
            project_repository=project_repository,
            project_permission_service=project_permission_service,
            event_bus=mock_event_bus
        )


