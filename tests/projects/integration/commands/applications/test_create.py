import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.commands.applications.create import CreateApplicationCommand, CreateApplicationCommandHandler
from app.projects.exceptions import NotFoundPositionException, NotFoundProjectException
from app.projects.models.application import  ApplicationStatus
from app.projects.models.position import Position
from app.projects.repositories.applications import ApplicationRepository
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository


@pytest.mark.integration
@pytest.mark.projects
class TestCreateApplicationCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        project_repository: ProjectRepository,
        position_repository: PositionRepository,
        application_repository: ApplicationRepository,
    ) -> CreateApplicationCommandHandler:
        return CreateApplicationCommandHandler(
            session=db_session,
            project_repository=project_repository,
            position_repository=position_repository,
            application_repository=application_repository,
        )

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        persisted_position: Position,
        make_user_jwt,
        handler: CreateApplicationCommandHandler,
        application_repository: ApplicationRepository,
    ) -> None:
        candidate_jwt = make_user_jwt(id="888", username="candidate")
        command = CreateApplicationCommand(
            position_id=persisted_position.id,
            message="I am a great fit",
            user_jwt_data=candidate_jwt,
        )

        await handler.handle(command)

        from sqlalchemy import select
        from app.projects.models.application import Application as App
        result = await application_repository.session.execute(
            select(App).where(
                App.position_id == persisted_position.id,
                App.candidate_id == 888,
            )
        )
        app = result.scalar()
        assert app is not None
        assert app.status == ApplicationStatus.pending
        assert app.message == "I am a great fit"

    @pytest.mark.asyncio
    async def test_create_position_not_found_raises(
        self,
        make_user_jwt,
        handler: CreateApplicationCommandHandler,
    ) -> None:
        from uuid import uuid4

        candidate_jwt = make_user_jwt(id="888", username="candidate")
        command = CreateApplicationCommand(
            position_id=uuid4(),
            message=None,
            user_jwt_data=candidate_jwt,
        )

        with pytest.raises(NotFoundPositionException):
            await handler.handle(command)

    # @pytest.mark.asyncio
    # async def test_create_project_not_found_raises(
    #     self,
    #     db_session: AsyncSession,
    #     make_user_jwt,
    #     position_repository: PositionRepository,
    #     project_repository: ProjectRepository,
    #     application_repository: ApplicationRepository,
    # ) -> None:

    #     orphan_position = Position.create(
    #         project_id=999999,
    #         title="Orphan",
    #         description="no project",
    #         required_skills={"skill"},
    #     )
    #     db_session.add(orphan_position)
    #     await db_session.flush()

    #     candidate_jwt = make_user_jwt(id="888", username="candidate")
    #     handler = CreateApplicationCommandHandler(
    #         session=db_session,
    #         project_repository=project_repository,
    #         position_repository=position_repository,
    #         application_repository=application_repository,
    #     )
    #     command = CreateApplicationCommand(
    #         position_id=orphan_position.id,
    #         message=None,
    #         user_jwt_data=candidate_jwt,
    #     )

    #     with pytest.raises(NotFoundProjectException):
    #         await handler.handle(command)

