from dataclasses import dataclass

from sqlalchemy import select

from app.core.db.repository import IRepository
from app.projects.models.role import ProjectRole


@dataclass
class ProjectRoleRepository(IRepository[ProjectRole]):
    async def get_by_id(self, project_id: int) -> ProjectRole | None:
        result = await self.session.execute(
            select(ProjectRole).where(ProjectRole.id==project_id)
        )
        return result.scalar()

    async def get_by_name(self, name: str) -> ProjectRole | None:
        result = await self.session.execute(
            select(ProjectRole).where(ProjectRole.name==name)
        )
        return result.scalar()

    async def create(self, project_role: ProjectRole) -> None:
        self.session.add(project_role)
