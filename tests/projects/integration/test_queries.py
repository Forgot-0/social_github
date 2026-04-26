import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.repository import PageResult
from app.core.filters.pagination import Pagination
from app.core.services.auth.dto import UserJWTData
from app.projects.dtos.positions import PositionDTO
from app.projects.dtos.projects import ProjectDTO
from app.projects.exceptions import NotFoundProjectException
from app.projects.filters.applications import ApplicationFilter
from app.projects.filters.positions import PositionFilter
from app.projects.filters.projects import ProjectFilter
from app.projects.models.application import Application, ApplicationStatus
from app.projects.models.position import Position
from app.projects.models.project import Project, ProjectVisibility
from app.projects.queries.applications.get_list import GetApplicationsQuery, GetApplicationsQueryHandler
from app.projects.queries.positions.get_by_id import GetPositionByIdQuery, GetPositionByIdQueryHandler
from app.projects.queries.positions.get_list import GetProjectPositionsQuery, GetProjectPositionsQueryHandler
from app.projects.queries.projects.get_by_id import GetProjectByIdQuery, GetProjectByIdQueryHandler
from app.projects.queries.projects.get_list import GetProjectsQuery, GetProjectsQueryHandler
from app.projects.repositories.applications import ApplicationRepository
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository
from app.projects.services.permission_service import ProjectPermissionService


@pytest.mark.integration
@pytest.mark.projects
class TestGetProjectByIdQuery:

    @pytest.fixture
    def handler(
        self,
        project_repository: ProjectRepository,
        project_permission_service: ProjectPermissionService,
    ) -> GetProjectByIdQueryHandler:
        return GetProjectByIdQueryHandler(
            project_repository=project_repository,
            project_permission_servise=project_permission_service,
        )

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: GetProjectByIdQueryHandler,
    ) -> None:
        result = await handler.handle(
            GetProjectByIdQuery(project_id=persisted_project.id, user_jwt_data=user_jwt)
        )

        assert isinstance(result, ProjectDTO)
        assert result.id == persisted_project.id
        assert result.owner_id == persisted_project.owner_id

    @pytest.mark.asyncio
    async def test_get_not_found_raises(
        self,
        user_jwt: UserJWTData,
        handler: GetProjectByIdQueryHandler,
    ) -> None:
        with pytest.raises(NotFoundProjectException):
            await handler.handle(
                GetProjectByIdQuery(project_id=999999, user_jwt_data=user_jwt)
            )

    @pytest.mark.asyncio
    async def test_private_project_not_visible_to_stranger(
        self,
        db_session: AsyncSession,
        make_user_jwt,
        handler: GetProjectByIdQueryHandler,
    ) -> None:
        private_project = Project.create(
            owner_id=1,
            name="Secret Project",
            slug="secret-project",
            small_description="",
            full_description="",
            visibility=ProjectVisibility.private,
            metadata={},
            tags=set(),
        )
        db_session.add(private_project)
        await db_session.commit()

        stranger_jwt = make_user_jwt(id="999", username="stranger")

        with pytest.raises(Exception):
            await handler.handle(
                GetProjectByIdQuery(project_id=private_project.id, user_jwt_data=stranger_jwt)
            )


@pytest.mark.integration
@pytest.mark.projects
class TestGetProjectsQuery:

    @pytest.fixture
    def handler(self, project_repository: ProjectRepository) -> GetProjectsQueryHandler:
        return GetProjectsQueryHandler(project_repository=project_repository)

    @pytest.mark.asyncio
    async def test_returns_public_projects(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: GetProjectsQueryHandler,
    ) -> None:
        f = ProjectFilter()
        f.set_pagination(Pagination(page=1, page_size=20))

        result = await handler.handle(GetProjectsQuery(filter=f, user_jwt_data=user_jwt))

        assert isinstance(result, PageResult)
        ids = [p.id for p in result.items]
        assert persisted_project.id in ids

    @pytest.mark.asyncio
    async def test_filter_by_name(
        self,
        persisted_project: Project,
        user_jwt: UserJWTData,
        handler: GetProjectsQueryHandler,
    ) -> None:
        f = ProjectFilter(name=persisted_project.name[:10])
        f.set_pagination(Pagination(page=1, page_size=20))

        result = await handler.handle(GetProjectsQuery(filter=f, user_jwt_data=user_jwt))

        ids = [p.id for p in result.items]
        assert persisted_project.id in ids

    @pytest.mark.asyncio
    async def test_pagination_works(
        self,
        user_jwt: UserJWTData,
        persisted_project: Project,
        handler: GetProjectsQueryHandler,
    ) -> None:
        f = ProjectFilter()
        f.set_pagination(Pagination(page=1, page_size=1))

        result = await handler.handle(GetProjectsQuery(filter=f, user_jwt_data=user_jwt))

        assert result.page_size == 1
        assert len(result.items) <= 1


@pytest.mark.integration
@pytest.mark.projects
class TestGetPositionByIdQuery:

    @pytest.fixture
    def handler(self, position_repository: PositionRepository) -> GetPositionByIdQueryHandler:
        return GetPositionByIdQueryHandler(position_repository=position_repository)

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self,
        persisted_position: Position,
        handler: GetPositionByIdQueryHandler,
    ) -> None:
        result = await handler.handle(
            GetPositionByIdQuery(position_id=persisted_position.id)
        )

        assert isinstance(result, PositionDTO)
        assert result.id == persisted_position.id
        assert result.title == persisted_position.title

    @pytest.mark.asyncio
    async def test_get_not_found_raises(
        self,
        handler: GetPositionByIdQueryHandler,
    ) -> None:
        from uuid import uuid4

        with pytest.raises(NotFoundProjectException):
            await handler.handle(GetPositionByIdQuery(position_id=uuid4()))


@pytest.mark.integration
@pytest.mark.projects
class TestGetProjectPositionsQuery:

    @pytest.fixture
    def handler(self, position_repository: PositionRepository) -> GetProjectPositionsQueryHandler:
        return GetProjectPositionsQueryHandler(position_repository=position_repository)

    @pytest.mark.asyncio
    async def test_returns_positions_for_project(
        self,
        persisted_position: Position,
        handler: GetProjectPositionsQueryHandler,
    ) -> None:
        f = PositionFilter(project_id=persisted_position.project_id)
        f.set_pagination(Pagination(page=1, page_size=20))

        result = await handler.handle(GetProjectPositionsQuery(filter=f))
        assert isinstance(result, PageResult)
        ids = [p.id for p in result.items]
        assert persisted_position.id in ids

    @pytest.mark.asyncio
    async def test_filter_by_title(
        self,
        persisted_position: Position,
        handler: GetProjectPositionsQueryHandler,
    ) -> None:
        f = PositionFilter(title="Backend")
        f.set_pagination(Pagination(page=1, page_size=20))

        result = await handler.handle(GetProjectPositionsQuery(filter=f))

        ids = [p.id for p in result.items]
        assert persisted_position.id in ids


@pytest.mark.integration
@pytest.mark.projects
class TestGetApplicationsQuery:

    @pytest.fixture
    def handler(self, application_repository: ApplicationRepository) -> GetApplicationsQueryHandler:
        return GetApplicationsQueryHandler(application_repository=application_repository)

    @pytest.mark.asyncio
    async def test_returns_applications_for_project(
        self,
        persisted_application: Application,
        handler: GetApplicationsQueryHandler,
        make_user_jwt
    ) -> None:
        f = ApplicationFilter(
            project_id=persisted_application.project_id,
            status=ApplicationStatus.pending,
        )
        f.set_pagination(Pagination(page=1, page_size=20))

        result = await handler.handle(GetApplicationsQuery(filter=f, user_jwt_data=make_user_jwt))

        assert isinstance(result, PageResult)
        ids = [a.id for a in result.items]
        assert persisted_application.id in ids

    @pytest.mark.asyncio
    async def test_filter_by_candidate(
        self,
        persisted_application: Application,
        handler: GetApplicationsQueryHandler,
        make_user_jwt
    ) -> None:
        f = ApplicationFilter(
            candidate_id=persisted_application.candidate_id,
            status=ApplicationStatus.pending,
        )
        f.set_pagination(Pagination(page=1, page_size=20))

        result = await handler.handle(GetApplicationsQuery(filter=f, user_jwt_data=make_user_jwt))

        ids = [a.id for a in result.items]
        assert persisted_application.id in ids

    @pytest.mark.asyncio
    async def test_filter_by_wrong_project_returns_empty(
        self,
        handler: GetApplicationsQueryHandler,
        make_user_jwt
    ) -> None:
        f = ApplicationFilter(
            project_id=999999,
            status=ApplicationStatus.pending,
        )
        f.set_pagination(Pagination(page=1, page_size=20))

        result = await handler.handle(GetApplicationsQuery(filter=f, user_jwt_data=make_user_jwt))

        assert result.total == 0
