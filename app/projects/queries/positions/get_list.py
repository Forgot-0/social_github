from dataclasses import dataclass
from uuid import UUID

from app.core.db.repository import PageResult
from app.core.queries import BaseQuery, BaseQueryHandler
from app.projects.dtos.positions import PositionDTO
from app.projects.filters.projects import ProjectFilter
from app.projects.models.position import Position
from app.projects.repositories.positions import PositionRepository


@dataclass(frozen=True)
class GetProjectPositionsQuery(BaseQuery):
    project_id: int
    filter: ProjectFilter


@dataclass(frozen=True)
class GetProjectPositionsQueryHandler(BaseQueryHandler[GetProjectPositionsQuery, PageResult[PositionDTO]]):
    position_repository: PositionRepository

    async def handle(self, query: GetProjectPositionsQuery) -> PageResult[PositionDTO]:
        page = await self.position_repository.find_by_filter(Position, query.filter)

        return PageResult(
            items=[
                PositionDTO.model_validate(position.to_dict())
                for position in page.items
            ],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )


