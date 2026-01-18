import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.profiles.repositories.profiles import ProfileRepository


@pytest_asyncio.fixture
async def profile_repository(db_session: AsyncSession) -> ProfileRepository:
    return ProfileRepository(session=db_session)
