import pytest
from dishka import AsyncContainer

from app.core.services.auth.dto import UserJWTData
from app.projects.commands.positions.update import UpdatePositionCommand, UpdatePositionCommandHandler
from app.projects.exceptions import (
    NotFoundProjectError,
)
from app.projects.models.position import Position, PositionLocationType
from app.projects.repositories.positions import PositionRepository
from tests.projects.integration.factories import PositionCommandFactory


@pytest.mark.integration
@pytest.mark.projects
@pytest.mark.asyncio
class TestUpdatePositionCommand:

    @pytest.fixture
    async def handler(
        self,
        request_container: AsyncContainer,
    ) -> UpdatePositionCommandHandler:
        return await request_container.get(UpdatePositionCommandHandler)

    async def test_update_title_success(
        self,
        persisted_position: Position,
        user_jwt: UserJWTData,
        handler: UpdatePositionCommandHandler,
        position_repository: PositionRepository,
    ) -> None:
        command = UpdatePositionCommand(
            position_id=persisted_position.id,
            user_jwt_data=user_jwt,
            **PositionCommandFactory.update_command(title="Updated Title"),
        )

        await handler.handle(command)

        updated = await position_repository.get_by_id(str(persisted_position.id))
        assert updated is not None
        assert updated.title == "Updated Title"

    async def test_update_required_skills(
        self,
        persisted_position: Position,
        user_jwt: UserJWTData,
        handler: UpdatePositionCommandHandler,
        position_repository: PositionRepository,
    ) -> None:
        command = UpdatePositionCommand(
            position_id=persisted_position.id,
            user_jwt_data=user_jwt,
            **PositionCommandFactory.update_command(required_skills={"rust", "wasm"}),
        )

        await handler.handle(command)

        updated = await position_repository.get_by_id(str(persisted_position.id))
        assert updated is not None
        assert set(updated.required_skills) == {"rust", "wasm"}

    async def test_update_location_type(
        self,
        persisted_position: Position,
        user_jwt: UserJWTData,
        handler: UpdatePositionCommandHandler,
        position_repository: PositionRepository,
    ) -> None:
        command = UpdatePositionCommand(
            position_id=persisted_position.id,
            user_jwt_data=user_jwt,
            **PositionCommandFactory.update_command(location_type="onsite"),
        )

        await handler.handle(command)

        updated = await position_repository.get_by_id(str(persisted_position.id))
        assert updated is not None
        assert updated.location_type == PositionLocationType.onsite

    async def test_update_none_fields_unchanged(
        self,
        persisted_position: Position,
        user_jwt: UserJWTData,
        handler: UpdatePositionCommandHandler,
        position_repository: PositionRepository,
    ) -> None:
        original_title = persisted_position.title

        command = UpdatePositionCommand(
            position_id=persisted_position.id,
            user_jwt_data=user_jwt,
            **PositionCommandFactory.update_command(description="Only description changed"),
        )

        await handler.handle(command)

        updated = await position_repository.get_by_id(str(persisted_position.id))
        assert updated is not None
        assert updated.title == original_title

    async def test_update_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler: UpdatePositionCommandHandler,
    ) -> None:
        from uuid import uuid4

        command = UpdatePositionCommand(
            position_id=uuid4(),
            user_jwt_data=user_jwt,
            **PositionCommandFactory.update_command(title="Doesn't matter"),
        )

        with pytest.raises(NotFoundProjectError):
            await handler.handle(command)

    async def test_update_without_permission_raises(
        self,
        persisted_position: Position,
        make_user_jwt,
        handler: UpdatePositionCommandHandler,
    ) -> None:
        stranger_jwt = make_user_jwt(id="999", username="stranger")
        command = UpdatePositionCommand(
            position_id=persisted_position.id,
            user_jwt_data=stranger_jwt,
            **PositionCommandFactory.update_command(title="Hijacked"),
        )

        with pytest.raises(Exception):
            await handler.handle(command)

