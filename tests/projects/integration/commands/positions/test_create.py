import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.projects.commands.positions.create import CreatePositionCommand, CreatePositionCommandHandler
from app.projects.config import project_config
from app.projects.exceptions import (
    MaxPositionsPerProjectLimitExceededException,
    NotFoundProjectException,
)
from app.projects.models.project import Project
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.services.permission_service import ProjectPermissionService
from tests.projects.integration.factories import PositionCommandFactory


@pytest.mark.integration
@pytest.mark.projects
class TestCreatePositionCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        project_repository: ProjectRepository,
        project_role_repository: ProjectRoleRepository,
        project_permission_service: ProjectPermissionService,
        mock_event_bus: BaseEventBus,
    ) -> CreatePositionCommandHandler:
        return CreatePositionCommandHandler(
            session=db_session,
            project_repository=project_repository,
            project_role_repository=project_role_repository,
            project_permission_service=project_permission_service,
            event_bus=mock_event_bus,
        )

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: CreatePositionCommandHandler,
        mock_event_bus,
        position_repository: PositionRepository,
    ) -> None:
        command = CreatePositionCommand(
            user_jwt_data=user_jwt,
            **PositionCommandFactory.create_command(
                project_id=persisted_project.id,
                title="Senior Backend Dev",
                required_skills={"python", "postgres"},
            ),
        )

        await handler.handle(command)

        project = await position_repository.session.get(Project, persisted_project.id)
        from sqlalchemy import select
        from app.projects.models.position import Position as Pos
        result = await position_repository.session.execute(
            select(Pos).where(Pos.project_id == persisted_project.id)
        )
        positions = result.scalars().all()
        assert len(positions) == 1
        assert positions[0].title == "Senior Backend Dev"

    @pytest.mark.asyncio
    async def test_create_fires_event(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: CreatePositionCommandHandler,
        mock_event_bus,
    ) -> None:
        command = CreatePositionCommand(
            user_jwt_data=user_jwt,
            **PositionCommandFactory.create_command(project_id=persisted_project.id),
        )

        await handler.handle(command)

        assert len(mock_event_bus.published_events) == 1
        event = mock_event_bus.published_events[0]
        assert event.__class__.__name__ == "CreatedPositionEvent"
        assert event.project_id == persisted_project.id

    @pytest.mark.asyncio
    async def test_create_project_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler: CreatePositionCommandHandler,
    ) -> None:
        command = CreatePositionCommand(
            user_jwt_data=user_jwt,
            **PositionCommandFactory.create_command(project_id=999999),
        )

        with pytest.raises(NotFoundProjectException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_create_limit_exceeded_raises(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: CreatePositionCommandHandler,
    ) -> None:
        for i in range(project_config.MAX_POSITIONS_PER_PROJECT):
            await handler.handle(
                CreatePositionCommand(
                    user_jwt_data=user_jwt,
                    **PositionCommandFactory.create_command(
                        project_id=persisted_project.id,
                        title=f"Position {i}",
                    ),
                )
            )

        with pytest.raises(MaxPositionsPerProjectLimitExceededException):
            await handler.handle(
                CreatePositionCommand(
                    user_jwt_data=user_jwt,
                    **PositionCommandFactory.create_command(
                        project_id=persisted_project.id,
                        title="Overflow",
                    ),
                )
            )

    @pytest.mark.asyncio
    async def test_create_without_permission_raises(
        self,
        persisted_project: Project,
        make_user_jwt,
        handler: CreatePositionCommandHandler,
    ) -> None:
        stranger_jwt = make_user_jwt(id="999", username="stranger")
        command = CreatePositionCommand(
            user_jwt_data=stranger_jwt,
            **PositionCommandFactory.create_command(project_id=persisted_project.id),
        )

        with pytest.raises(Exception):
            await handler.handle(command)
