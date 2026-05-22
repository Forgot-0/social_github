import pytest
from dishka import AsyncContainer

from app.core.services.auth.dto import UserJWTData
from app.projects.commands.positions.delete import DeletePositionCommand, DeletePositionCommandHandler
from app.projects.exceptions import (
    NotFoundProjectError,
)
from app.projects.models.position import Position
from app.projects.repositories.positions import PositionRepository



@pytest.mark.integration
@pytest.mark.projects
@pytest.mark.asyncio
class TestDeletePositionCommand:

    @pytest.fixture
    async def handler(
        self,
        request_container: AsyncContainer,
    ) -> DeletePositionCommandHandler:
        return await request_container.get(DeletePositionCommandHandler)

    async def test_delete_success(
        self,
        persisted_position: Position,
        user_jwt: UserJWTData,
        handler: DeletePositionCommandHandler,
        position_repository: PositionRepository,
    ) -> None:
        command = DeletePositionCommand(
            position_id=persisted_position.id,
            user_jwt_data=user_jwt,
        )

        await handler.handle(command)

        deleted = await position_repository.get_by_id(str(persisted_position.id))
        assert deleted is None

    async def test_delete_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler: DeletePositionCommandHandler,
    ) -> None:
        from uuid import uuid4

        command = DeletePositionCommand(
            position_id=uuid4(),
            user_jwt_data=user_jwt,
        )

        with pytest.raises(NotFoundProjectError):
            await handler.handle(command)

    async def test_delete_without_permission_raises(
        self,
        persisted_position: Position,
        make_user_jwt,
        handler: DeletePositionCommandHandler,
    ) -> None:
        stranger_jwt = make_user_jwt(id="999", username="stranger")
        command = DeletePositionCommand(
            position_id=persisted_position.id,
            user_jwt_data=stranger_jwt,
        )

        with pytest.raises(Exception):
            await handler.handle(command)