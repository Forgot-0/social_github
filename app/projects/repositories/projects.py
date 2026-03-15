from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.member import ProjectMembership
from app.projects.models.project import Project


@dataclass
class ProjectRepository(IRepository[Project]):
    async def get_by_id(self, id: int, with_member: bool=False, with_positon: bool=False) -> Project | None:
        stmt = select(Project).where(Project.id==id)
        if with_member:
            stmt = stmt.options(selectinload(Project.memberships))

        if with_positon:
            stmt = stmt.options(selectinload(Project.positions))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_by_name(self, name: str) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.name==name)
        )
        return result.scalar()

    async def create(self, project: Project) -> None:
        self.session.add(project)

    async def get_membership(self, project_id: int, user_id: int) -> ProjectMembership | None:
        result = await self.session.execute(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.user_id == user_id,
            )
        )
        return result.scalar()

    async def list_members(self, project_id: int) -> list[ProjectMembership]:

        result = await self.session.execute(
            select(ProjectMembership).where(ProjectMembership.project_id == project_id)
        )
        return list(result.scalars().all())

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
