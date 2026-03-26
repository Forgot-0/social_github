from dataclasses import dataclass

from app.core.db.repository import PageResult
from app.core.queries import BaseQuery, BaseQueryHandler
from app.rooms.dtos.rooms import RoomDTO
from app.rooms.filters.rooms import RoomFilter
from app.rooms.models.rooms import Room
from app.rooms.repositories.rooms import RoomRepository


@dataclass(frozen=True)
class ListRoomsQuery(BaseQuery):
    filters: RoomFilter


@dataclass(frozen=True)
class ListRoomsQueryHandler(BaseQueryHandler[ListRoomsQuery, PageResult[RoomDTO]]):
    room_repository: RoomRepository

    async def handle(self, query: ListRoomsQuery) -> PageResult[RoomDTO]:
        result = await self.room_repository.find_by_filter(Room, filters=query.filters)

        return PageResult(
            items=[RoomDTO.model_validate(**r.to_dict()) for r in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
