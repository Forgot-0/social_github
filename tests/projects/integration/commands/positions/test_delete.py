import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.auth.dto import UserJWTData
from app.projects.commands.positions.delete import DeletePositionCommand, DeletePositionCommandHandler
from app.projects.exceptions import (
    NotFoundProjectException,
)
from app.projects.models.position import Position
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository
from app.projects.services.permission_service import ProjectPermissionService



@pytest.mark.integration
@pytest.mark.projects
class TestDeletePositionCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        position_repository: PositionRepository,
        project_repository: ProjectRepository,
        project_permission_service: ProjectPermissionService,
    ) -> DeletePositionCommandHandler:
        return DeletePositionCommandHandler(
            session=db_session,
            position_repository=position_repository,
            project_repository=project_repository,
            project_permission_service=project_permission_service,
        )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

        with pytest.raises(NotFoundProjectException):
            await handler.handle(command)

    @pytest.mark.asyncio
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