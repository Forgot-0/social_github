from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.dtos.roles import RoleDTO
from app.core.db.repository import PageResult
from app.projects.filters.roles import RolesFilter


@dataclass(frozen=True)
class GetProjectRolesQuery(BaseQuery):
    filter: RolesFilter


@dataclass(frozen=True)
class GetProjectRolesQueryHandler(BaseQueryHandler[GetProjectRolesQuery, PageResult[RoleDTO]]):
    project_role_repository: ProjectRoleRepository

    async def handle(self, query: GetProjectRolesQuery) -> PageResult[RoleDTO]:
        from app.projects.models.role import ProjectRole
+        page = await self.project_role_repository.find_by_filter(ProjectRole, query.filter)
        return PageResult(
            items=[RoleDTO.model_validate(r.to_dict()) for r in page.items],
            total=page.total,
            page=page.page,
            page_size=page.page_size
        )
