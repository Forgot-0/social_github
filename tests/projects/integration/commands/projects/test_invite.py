import pytest
from dishka import AsyncContainer

from app.core.services.auth.dto import UserJWTData
from app.projects.commands.projects.invite import InviteMemberCommand, InviteMemberCommandHandler
from app.projects.exceptions import NotFoundProjectError
from app.projects.models.member import MembershipStatus
from app.projects.models.project import Project
from app.projects.models.role_permissions import ProjectRolesEnum
from app.projects.repositories.projects import ProjectRepository


@pytest.mark.integration
@pytest.mark.projects
@pytest.mark.asyncio
class TestInviteMemberCommand:

    @pytest.fixture
    async def handler(
        self,
        request_container: AsyncContainer,
    ) -> InviteMemberCommandHandler:
        return await request_container.get(InviteMemberCommandHandler)

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

        with pytest.raises(NotFoundProjectError):
            await handler.handle(command)

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

