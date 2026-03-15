import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.applications import ApplicationRepository


@pytest_asyncio.fixture
async def project_repository(db_session: AsyncSession) -> ProjectRepository:
    return ProjectRepository(session=db_session)


@pytest_asyncio.fixture
async def position_repository(db_session: AsyncSession) -> PositionRepository:
    return PositionRepository(session=db_session)


@pytest_asyncio.fixture
async def application_repository(db_session: AsyncSession) -> ApplicationRepository:
    return ApplicationRepository(session=db_session)

