from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, select

from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.application import Application


@dataclass
class ApplicationRepository(IRepository[Application]):
    async def get_by_id(self, id: UUID) -> Application | None:
        stmt = select(Application).where(Application.id == id)
        result = await self.session.execute(stmt)
        return result.scalar()

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt


    async def create(self, application: Application) -> None:
        self.session.add(application)
