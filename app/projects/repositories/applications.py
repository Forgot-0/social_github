from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.application import Application


@dataclass
class ApplicationRepository(IRepository[Application], CacheRepository):
    _LIST_VERSION_KEY = "applications:list"

    async def get_by_id(self, id: UUID, with_position: bool = False) -> Application | None:
        stmt = select(Application).where(Application.id == id)

        if with_position:
            stmt = stmt.options(selectinload(Application.position))

        result = await self.session.execute(stmt)
        return result.scalar()

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt


    async def create(self, application: Application) -> None:
        self.session.add(application)
