from dataclasses import dataclass

from app.core.db.repository import PageResult
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.dtos.projects import ProjectDTO
from app.projects.filters.projects import ProjectFilter
from app.projects.models.project import Project
from app.projects.repositories.projects import ProjectRepository


@dataclass(frozen=True)
class GetProjectsQuery(BaseQuery):
    filter: ProjectFilter
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class GetProjectsQueryHandler(BaseQueryHandler[GetProjectsQuery, PageResult[ProjectDTO]]):
    project_repository: ProjectRepository

    async def handle(self, query: GetProjectsQuery) -> PageResult[ProjectDTO]:
        return await self.project_repository.cache_paginated(
            ProjectDTO, self._handle, ttl=400,
            query=query
        )

    async def _handle(self, query: GetProjectsQuery) -> PageResult[ProjectDTO]:
        page = await self.project_repository.find_by_filter(Project, query.filter)
        return PageResult(
            items=[ProjectDTO.model_validate(project.to_dict()) for project in page.items],
            total=page.total,
            page=page.page,
            page_size=page.page_size
        )
