from dataclasses import dataclass

from sqlalchemy import Select, select

from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.position import Position


@dataclass
class PositionRepository(IRepository[Position]):
    async def get_by_id(self, id: str) -> Position | None:
        stmt = select(Position).where(Position.id == id)
        result = await self.session.execute(stmt)
        return result.scalar()

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt

