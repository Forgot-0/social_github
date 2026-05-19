import pytest
from dishka import AsyncContainer

from app.core.services.auth.dto import UserJWTData
from app.projects.commands.applications.decision import DecideApplicationCommand, DecideApplicationCommandHandler
from app.projects.exceptions import NotFoundProjectException
from app.projects.models.application import Application, ApplicationStatus
from app.projects.models.member import MembershipStatus
from app.projects.repositories.applications import ApplicationRepository
from app.projects.repositories.projects import ProjectRepository


@pytest.mark.integration
@pytest.mark.projects
@pytest.mark.asyncio
class TestDecideApplicationCommand:

    @pytest.fixture
    async def handler(
        self,
        request_container: AsyncContainer,
    ) -> DecideApplicationCommandHandler:
        return await request_container.get(DecideApplicationCommandHandler)

    async def test_approve_changes_application_status(
        self,
        persisted_application: Application,
        user_jwt: UserJWTData,
        handler: DecideApplicationCommandHandler,
        application_repository: ApplicationRepository,
    ) -> None:
        command = DecideApplicationCommand(
            application_id=persisted_application.id,
            approve=True,
            user_jwt_data=user_jwt,
        )

        await handler.handle(command)

        updated = await application_repository.get_by_id(persisted_application.id, with_position=True)
        assert updated is not None
        assert updated.status == ApplicationStatus.accepted
        assert updated.decided_by == int(user_jwt.id)
        assert updated.decided_at is not None
        assert updated.position.is_open == False

    async def test_approve_creates_membership(
        self,
        persisted_application: Application,
        user_jwt: UserJWTData,
        handler: DecideApplicationCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        command = DecideApplicationCommand(
            application_id=persisted_application.id,
            approve=True,
            user_jwt_data=user_jwt,
        )

        await handler.handle(command)

        membership = await project_repository.get_membership(
            persisted_application.project_id,
            persisted_application.candidate_id,
        )
        assert membership is not None
        assert membership.status == MembershipStatus.active

    async def test_reject_changes_application_status(
        self,
        persisted_application: Application,
        user_jwt: UserJWTData,
        handler: DecideApplicationCommandHandler,
        application_repository: ApplicationRepository,
    ) -> None:
        command = DecideApplicationCommand(
            application_id=persisted_application.id,
            approve=False,
            user_jwt_data=user_jwt,
        )

        await handler.handle(command)

        updated = await application_repository.get_by_id(persisted_application.id)
        assert updated is not None
        assert updated.status == ApplicationStatus.rejected
        assert updated.decided_by == int(user_jwt.id)

    async def test_reject_does_not_create_membership(
        self,
        persisted_application: Application,
        user_jwt: UserJWTData,
        handler: DecideApplicationCommandHandler,
        project_repository: ProjectRepository,
    ) -> None:
        command = DecideApplicationCommand(
            application_id=persisted_application.id,
            approve=False,
            user_jwt_data=user_jwt,
        )

        await handler.handle(command)

        membership = await project_repository.get_membership(
            persisted_application.project_id,
            persisted_application.candidate_id,
        )
        assert membership is None

    async def test_decide_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler: DecideApplicationCommandHandler,
    ) -> None:
        from uuid import uuid4

        command = DecideApplicationCommand(
            application_id=uuid4(),
            approve=True,
            user_jwt_data=user_jwt,
        )

        with pytest.raises(NotFoundProjectException):
            await handler.handle(command)

    async def test_approve_without_permission_raises(
        self,
        persisted_application: Application,
        make_user_jwt,
        handler: DecideApplicationCommandHandler,
    ) -> None:
        stranger_jwt = make_user_jwt(id="999", username="stranger")
        command = DecideApplicationCommand(
            application_id=persisted_application.id,
            approve=True,
            user_jwt_data=stranger_jwt,
        )

        with pytest.raises(Exception):
            await handler.handle(command)

    async def test_decide_already_decided_application_raises(
        self,
        persisted_application: Application,
        user_jwt: UserJWTData,
        handler: DecideApplicationCommandHandler,
    ) -> None:
        command = DecideApplicationCommand(
            application_id=persisted_application.id,
            approve=False,
            user_jwt_data=user_jwt,
        )
        await handler.handle(command)

        with pytest.raises(Exception):
            await handler.handle(command)