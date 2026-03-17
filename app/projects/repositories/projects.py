from dataclasses import dataclass

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter
from app.projects.models.member import MembershipStatus, ProjectMembership
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

    async def get_by_slug(self, slug: str) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.slug==slug)
        )
        return result.scalar()

    async def count_by_owner(self, owner_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Project).where(Project.owner_id == owner_id)
        )
        return result.scalar_one()

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

    async def list_my_projects(self, user_id: int, page: int = 1, page_size: int = 20):
        """
        List projects where user is owner or active member.
        """
        stmt = (
            select(Project)
            .outerjoin(ProjectMembership, ProjectMembership.project_id == Project.id)
            .where(
                or_(
                    Project.owner_id == user_id,
                    and_(
                        ProjectMembership.user_id == user_id,
                        ProjectMembership.status == MembershipStatus.active,
                    ),
                )
            )
            .distinct()
            .options(selectinload(Project.memberships).selectinload(ProjectMembership.role))
            .order_by(Project.created_at.desc())
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(stmt.offset(offset).limit(page_size))
        items = result.scalars().all()

        from app.core.db.repository import PageResult

        return PageResult(items=list(items), total=total, page=page, page_size=page_size)

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
