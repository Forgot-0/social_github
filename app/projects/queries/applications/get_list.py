from dataclasses import dataclass

from app.core.db.repository import PageResult
from app.core.queries import BaseQuery, BaseQueryHandler
from app.projects.dtos.applications import ApplicationDTO
from app.projects.filters.applications import ApplicationFilter
from app.projects.models.application import Application
from app.projects.repositories.applications import ApplicationRepository


@dataclass(frozen=True)
class GetApplicationsQuery(BaseQuery):
    filter: ApplicationFilter


@dataclass(frozen=True)
class GetApplicationsQueryHandler(BaseQueryHandler[GetApplicationsQuery, PageResult[ApplicationDTO]]):
    application_repository: ApplicationRepository

    async def handle(self, query: GetApplicationsQuery) -> PageResult[ApplicationDTO]:
        page = await self.application_repository.find_by_filter(Application, query.filter)

        return PageResult(
            items=[
                ApplicationDTO.model_validate(application.to_dict())
                for application in page.items
            ],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )

