import pytest
from dishka import AsyncContainer

from app.core.services.auth.dto import UserJWTData
from app.projects.commands.members.accept import AcceptInviteCommand, AcceptInviteCommandHandler
from app.projects.commands.projects.invite import InviteMemberCommand, InviteMemberCommandHandler
from app.projects.exceptions import NotFoundProjectException
from app.projects.models.member import MembershipStatus
from app.projects.models.project import Project
from app.projects.models.role_permissions import ProjectRolesEnum
from app.projects.repositories.projects import ProjectRepository



@pytest.mark.integration
@pytest.mark.projects
@pytest.mark.asyncio
class TestAcceptInviteCommand:

    @pytest.fixture
    async def handler(
        self,
        request_container: AsyncContainer,
    ) -> AcceptInviteCommandHandler:
        return await request_container.get(AcceptInviteCommandHandler)

    @pytest.fixture
    async def invite_handler(
        self,
        request_container: AsyncContainer
    ) -> InviteMemberCommandHandler:
        return await request_container.get(InviteMemberCommandHandler)

    async def test_accept_invite_changes_status_to_active(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        invite_handler: InviteMemberCommandHandler,
        handler: AcceptInviteCommandHandler,
        project_repository: ProjectRepository,
        make_user_jwt,
    ) -> None:
        invited_user_id = 600
        invited_jwt = make_user_jwt(id=str(invited_user_id), username="invitee")

        await invite_handler.handle(
            InviteMemberCommand(
                user_jwt_data=user_jwt,
                project_id=persisted_project.id,
                user_id=invited_user_id,
                role_id=ProjectRolesEnum.USER.value.id,
            )
        )

        await handler.handle(
            AcceptInviteCommand(
                user_jwt_data=invited_jwt,
                project_id=persisted_project.id,
            )
        )

        membership = await project_repository.get_membership(persisted_project.id, invited_user_id)
        assert membership is not None
        assert membership.status == MembershipStatus.active
        assert membership.joined_at is not None

    async def test_accept_without_invite_raises(
        self,
        persisted_project: Project,
        make_user_jwt,
        handler: AcceptInviteCommandHandler,
    ) -> None:
        stranger_jwt = make_user_jwt(id="700", username="stranger")

        with pytest.raises(NotFoundProjectException):
            await handler.handle(
                AcceptInviteCommand(
                    user_jwt_data=stranger_jwt,
                    project_id=persisted_project.id,
                )
            )