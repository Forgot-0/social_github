from dataclasses import dataclass

from app.core.db.repository import PageResult
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData
from app.projects.dtos.projects import ProjectDTO
from app.projects.models.project import Project
from app.projects.repositories.projects import ProjectRepository


@dataclass(frozen=True)
class GetMyProjectsQuery(BaseQuery):
    user_jwt_data: UserJWTData
    page: int
    page_size: int


@dataclass(frozen=True)
class GetMyProjectsQueryHandler(BaseQueryHandler[GetMyProjectsQuery, PageResult[ProjectDTO]]):
    project_repository: ProjectRepository

    async def handle(self, query: GetMyProjectsQuery) -> PageResult[ProjectDTO]:
        return await self.project_repository.cache_paginated(
            ProjectDTO, func=self._handle, ttl=1200,
            query=query
        )

    async def _handle(self, query: GetMyProjectsQuery) -> PageResult[ProjectDTO]:
        page = await self.project_repository.list_my_projects(
            user_id=int(query.user_jwt_data.id),
            page=query.page,
            page_size=query.page_size,
        )
        return PageResult(
            items=[ProjectDTO.model_validate(project.to_dict()) for project in page.items],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )