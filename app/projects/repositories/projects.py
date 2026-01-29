from dataclasses import dataclass

from sqlalchemy import Select, select

from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.project import Project


@dataclass
class ProjectRepository(IRepository[Project]):
    async def get_by_id(self, id: int) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.id==id)
        )
        return result.scalar()

    async def get_by_name(self, name: str) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.name==name)
        )
        return result.scalar()

    async def create(self, project_role: Project) -> None:
        self.session.add(project_role)

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
