import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.projects.commands.projects.invite import InviteMemberCommand, InviteMemberCommandHandler
from app.projects.exceptions import NotFoundProjectException
from app.projects.models.member import MembershipStatus
from app.projects.models.project import Project
from app.projects.models.role_permissions import ProjectRolesEnum
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.services.permission_service import ProjectPermissionService


@pytest.mark.integration
@pytest.mark.projects
class TestInviteMemberCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        project_repository: ProjectRepository,
        project_role_repository: ProjectRoleRepository,
        project_permission_service: ProjectPermissionService,
        mock_event_bus: BaseEventBus,
    ) -> InviteMemberCommandHandler:
        return InviteMemberCommandHandler(
            session=db_session,
            project_repository=project_repository,
            project_role_repository=project_role_repository,
            project_permission_service=project_permission_service,
            event_bus=mock_event_bus,
        )

    @pytest.mark.asyncio
    async def test_invite_success(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: InviteMemberCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        command = InviteMemberCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            user_id=500,
            role_id=ProjectRolesEnum.USER.value.id,
        )

        await handler.handle(command)

        membership = await project_repository.get_membership(persisted_project.id, 500)
        assert membership is not None
        assert membership.status == MembershipStatus.invited
        assert membership.invited_by == int(user_jwt.id)

    @pytest.mark.asyncio
    async def test_invite_project_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler: InviteMemberCommandHandler,
    ) -> None:
        command = InviteMemberCommand(
            user_jwt_data=user_jwt,
            project_id=999999,
            user_id=500,
            role_id=ProjectRolesEnum.USER.value.id,
        )

        with pytest.raises(NotFoundProjectException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_invite_nonexistent_role_raises(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: InviteMemberCommandHandler,
    ) -> None:
        command = InviteMemberCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            user_id=500,
            role_id=99999,
        )

        with pytest.raises(Exception):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_invite_already_member_raises(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: InviteMemberCommandHandler,
    ) -> None:
        command = InviteMemberCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            user_id=501,
            role_id=ProjectRolesEnum.USER.value.id,
        )
        await handler.handle(command)

        with pytest.raises(Exception):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_invite_with_permissions_overrides(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: InviteMemberCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        overrides = {"project:update": True}
        command = InviteMemberCommand(
            user_jwt_data=user_jwt,
            project_id=persisted_project.id,
            user_id=502,
            role_id=ProjectRolesEnum.USER.value.id,
            permissions_overrides=overrides,
        )

        await handler.handle(command)

        membership = await project_repository.get_membership(persisted_project.id, 502)
        assert membership is not None
        assert membership.permissions_overrides == overrides

