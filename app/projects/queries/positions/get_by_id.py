from dataclasses import dataclass
from uuid import UUID

from app.core.queries import BaseQuery, BaseQueryHandler
from app.projects.dtos.positions import PositionDTO
from app.projects.exceptions import NotFoundProjectException
from app.projects.repositories.positions import PositionRepository


@dataclass(frozen=True)
class GetPositionByIdQuery(BaseQuery):
    position_id: UUID


@dataclass(frozen=True)
class GetPositionByIdQueryHandler(BaseQueryHandler[GetPositionByIdQuery, PositionDTO]):
    position_repository: PositionRepository

    async def handle(self, query: GetPositionByIdQuery) -> PositionDTO:
        position = await self.position_repository.get_by_id(str(query.position_id))
        if not position:
            raise NotFoundProjectException(project_id=0)

        return PositionDTO.model_validate(position.to_dict())

