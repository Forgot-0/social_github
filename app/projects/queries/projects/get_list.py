from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.projects.repositories.projects import ProjectRepository
from app.projects.dtos.projects import ProjectDTO
from app.core.db.repository import PageResult
from app.projects.filters.projects import ProjectFilter
from app.projects.models.project import Project


@dataclass(frozen=True)
class GetProjectsQuery(BaseQuery):
    filter: ProjectFilter


@dataclass(frozen=True)
class GetProjectsQueryHandler(BaseQueryHandler[GetProjectsQuery, PageResult[ProjectDTO]]):
    project_repository: ProjectRepository

    async def handle(self, query: GetProjectsQuery) -> PageResult[ProjectDTO]:
        page = await self.project_repository.find_by_filter(Project, query.filter)
        return PageResult(
            items=[
                ProjectDTO.model_validate(
                    {
                        **p.to_dict(),
                        "memberships": [
                            {
                                "id": m.id,
                                "project_id": m.project_id,
                                "user_id": m.user_id,
                                "role_id": m.role_id,
                                "status": getattr(m.status, "name", str(m.status)),
                                "invited_by": m.invited_by,
                                "joined_at": m.joined_at,
                                "permissions": m.effective_permissions(),
                            }
                            for m in p.memberships
                        ],
                    }
                )
                for p in page.items
            ],
            total=page.total,
            page=page.page,
            page_size=page.page_size
        )
