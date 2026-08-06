import pytest
from dishka import AsyncContainer

from app.core.services.auth.dto import UserJWTData
from app.projects.commands.positions.create import CreatePositionCommand, CreatePositionCommandHandler
from app.projects.config import project_config
from app.projects.exceptions import (
    MaxPositionsPerProjectLimitExceededError,
    NotFoundProjectError,
)
from app.projects.models.project import Project
from app.projects.repositories.positions import PositionRepository
from tests.projects.integration.factories import PositionCommandFactory


@pytest.mark.integration
@pytest.mark.projects
@pytest.mark.asyncio
class TestCreatePositionCommand:

    @pytest.fixture
    async def handler(
        self,
        request_container: AsyncContainer,
    ) -> CreatePositionCommandHandler:
        return await request_container.get(CreatePositionCommandHandler)

    async def test_create_success(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: CreatePositionCommandHandler,
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

    async def test_create_fires_event(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: CreatePositionCommandHandler,
    ) -> None:
        command = CreatePositionCommand(
            user_jwt_data=user_jwt,
            **PositionCommandFactory.create_command(project_id=persisted_project.id),
        )

        await handler.handle(command)


    async def test_create_project_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler: CreatePositionCommandHandler,
    ) -> None:
        command = CreatePositionCommand(
            user_jwt_data=user_jwt,
            **PositionCommandFactory.create_command(project_id=999999),
        )

        with pytest.raises(NotFoundProjectError):
            await handler.handle(command)

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

        with pytest.raises(MaxPositionsPerProjectLimitExceededError):
            await handler.handle(
                CreatePositionCommand(
                    user_jwt_data=user_jwt,
                    **PositionCommandFactory.create_command(
                        project_id=persisted_project.id,
                        title="Overflow",
                    ),
                )
            )

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
