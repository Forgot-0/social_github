from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.position import Position
from app.projects.models.project import Project


@dataclass
class PositionRepository(IRepository[Position], CacheRepository):
    _LIST_VERSION_KEY = "positions:list"

    async def get_by_id(self, id: str, with_project: bool=False) -> Position | None:
        stmt = select(Position).where(Position.id == id)
        if with_project:
            stmt = stmt.options(selectinload(Position.project).selectinload(Project.memberships))

        result = await self.session.execute(stmt)
        return result.scalar()

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt

