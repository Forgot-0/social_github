from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.core.db.repository import CacheRepository, IRepository
from app.profiles.filters.profiles import ProfileFilter
from app.profiles.models.profile import Profile


@dataclass
class ProfileRepository(IRepository[Profile], CacheRepository):
    _LIST_VERSION_KEY = "profile:list"

    async def create(self, profile: Profile) -> None:
        self.session.add(profile)

    async def get_by_id(self, profile_id: int) -> Profile | None:
        query = select(Profile).where(Profile.id==profile_id).options(selectinload(Profile.contacts))
        result = await self.session.execute(query)
        return result.scalar()

    def apply_relationship_filters(self, stmt: Select, filters: ProfileFilter) -> Select:
        return stmt
