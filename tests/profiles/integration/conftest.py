import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.auth.rbac import RBACManager
from app.profiles.commands.profiles.update import UpdateProfileCommandHandler
from app.profiles.models.profile import Profile
from app.profiles.repositories.profiles import ProfileRepository


@pytest.fixture
async def persisted_profile(db_session: AsyncSession, user_jwt) -> Profile:
    profile = Profile.create(
        user_id=int(user_jwt.id),
        username=user_jwt.username,
        display_name="test_name",
        bio="Python Developer",
        skills={"python", "sql", "fastapi"},
    )
    db_session.add(profile)
    await db_session.commit()
    return profile

@pytest.fixture
def handler_factory(
    db_session: AsyncSession,
    profile_repository: ProfileRepository,
    rbac_manager: RBACManager,
):
    def _make():
        return UpdateProfileCommandHandler(
            session=db_session,
            profile_repository=profile_repository,
            rbac_manager=rbac_manager,
        )
    return _make