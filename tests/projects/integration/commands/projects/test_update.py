import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.projects.commands.projects.update import UpdateProjectCommand, UpdateProjectCommandHandler
from app.projects.exceptions import NotFoundProjectException
from app.projects.models.project import Project, ProjectVisibility
from app.projects.repositories.projects import ProjectRepository
from app.projects.services.permission_service import ProjectPermissionService
from tests.projects.integration.factories import ProjectCommandFactory


@pytest.mark.integration
@pytest.mark.projects
class TestUpdateProjectCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        project_repository: ProjectRepository,
        project_permission_service: ProjectPermissionService,
        mock_event_bus: BaseEventBus,
    ) -> UpdateProjectCommandHandler:
        return UpdateProjectCommandHandler(
            session=db_session,
            project_repository=project_repository,
            project_permission_service=project_permission_service,
            event_bus=mock_event_bus,
        )

    @pytest.mark.asyncio
    async def test_update_name_success(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: UpdateProjectCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        command = UpdateProjectCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            **ProjectCommandFactory.update_command(name="Renamed Project"),
        )

        await handler.handle(command)

        updated = await project_repository.get_by_id(persisted_project.id)
        assert updated is not None
        assert updated.name == "Renamed Project"

    @pytest.mark.asyncio
    async def test_update_description_success(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: UpdateProjectCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        command = UpdateProjectCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            **ProjectCommandFactory.update_command(description="New description"),
        )

        await handler.handle(command)

        updated = await project_repository.get_by_id(persisted_project.id)
        assert updated is not None
        assert updated.small_description == "New description"

    @pytest.mark.asyncio
    async def test_update_visibility_to_private(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: UpdateProjectCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        command = UpdateProjectCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            **ProjectCommandFactory.update_command(visibility="private"),
        )

        await handler.handle(command)

        updated = await project_repository.get_by_id(persisted_project.id)
        assert updated is not None
        assert updated.visibility == ProjectVisibility.private

    @pytest.mark.asyncio
    async def test_update_tags_success(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: UpdateProjectCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        command = UpdateProjectCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            **ProjectCommandFactory.update_command(tags={"rust", "wasm"}),
        )

        await handler.handle(command)

        updated = await project_repository.get_by_id(persisted_project.id)
        assert updated is not None
        assert set(updated.tags) == {"rust", "wasm"}

    @pytest.mark.asyncio
    async def test_none_fields_not_changed(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: UpdateProjectCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        original_name = persisted_project.name

        command = UpdateProjectCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            **ProjectCommandFactory.update_command(description="Only description changed"),
        )

        await handler.handle(command)

        updated = await project_repository.get_by_id(persisted_project.id)
        assert updated is not None
        assert updated.name == original_name

    @pytest.mark.asyncio
    async def test_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler: UpdateProjectCommandHandler,
    ) -> None:
        command = UpdateProjectCommand(
            user_jwt_data=user_jwt,
            project_id=999999,
            **ProjectCommandFactory.update_command(name="Doesn't matter"),
        )

        with pytest.raises(NotFoundProjectException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_non_owner_without_permission_cannot_update(
        self,
        persisted_project: Project,
        make_user_jwt,
        handler: UpdateProjectCommandHandler,
    ) -> None:
        other_jwt = make_user_jwt(id="999", username="stranger")

        command = UpdateProjectCommand(
            user_jwt_data=other_jwt,
            project_id=persisted_project.id,
            **ProjectCommandFactory.update_command(name="Hijacked"),
        )

        with pytest.raises(Exception):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_super_admin_can_update_any_project(
        self,
        persisted_project: Project,
        super_admin_user_jwt: UserJWTData,
        handler: UpdateProjectCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        command = UpdateProjectCommand(
            user_jwt_data=super_admin_user_jwt,
            project_id=persisted_project.id,
            **ProjectCommandFactory.update_command(name="Admin Updated"),
        )

        await handler.handle(command)

        updated = await project_repository.get_by_id(persisted_project.id)
        assert updated is not None
        assert updated.name == "Admin Updated"