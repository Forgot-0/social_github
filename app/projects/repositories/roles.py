from dataclasses import dataclass

from sqlalchemy import Select, select

from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.role import ProjectRole


@dataclass
class ProjectRoleRepository(IRepository[ProjectRole]):
    async def get_by_id(self, id: int) -> ProjectRole | None:
        result = await self.session.execute(
            select(ProjectRole).where(ProjectRole.id==id)
        )
        return result.scalar()

    async def get_by_name(self, name: str) -> ProjectRole | None:
        result = await self.session.execute(
            select(ProjectRole).where(ProjectRole.name==name)
        )
        return result.scalar()

    async def create(self, project_role: ProjectRole) -> None:
        self.session.add(project_role)

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
