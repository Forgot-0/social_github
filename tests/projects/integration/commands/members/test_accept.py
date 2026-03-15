import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.projects.commands.members.accept import AcceptInviteCommand, AcceptInviteCommandHandler
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
class TestAcceptInviteCommand:

    @pytest.fixture
    def accept_handler(
        self,
        db_session: AsyncSession,
        project_repository: ProjectRepository,
        mock_event_bus: BaseEventBus,
    ) -> AcceptInviteCommandHandler:
        return AcceptInviteCommandHandler(
            session=db_session,
            project_repository=project_repository,
            event_bus=mock_event_bus,
        )

    @pytest.fixture
    def invite_handler(
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
    async def test_accept_invite_changes_status_to_active(
        self,
        db_session: AsyncSession,
        persisted_project: Project,
        user_jwt: UserJWTData,
        invite_handler: InviteMemberCommandHandler,
        accept_handler: AcceptInviteCommandHandler,
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

        await accept_handler.handle(
            AcceptInviteCommand(
                user_jwt_data=invited_jwt,
                project_id=persisted_project.id,
            )
        )

        membership = await project_repository.get_membership(persisted_project.id, invited_user_id)
        assert membership is not None
        assert membership.status == MembershipStatus.active
        assert membership.joined_at is not None

    @pytest.mark.asyncio
    async def test_accept_without_invite_raises(
        self,
        persisted_project: Project,
        make_user_jwt,
        accept_handler: AcceptInviteCommandHandler,
    ) -> None:
        stranger_jwt = make_user_jwt(id="700", username="stranger")

        with pytest.raises(NotFoundProjectException):
            await accept_handler.handle(
                AcceptInviteCommand(
                    user_jwt_data=stranger_jwt,
                    project_id=persisted_project.id,
                )
            )