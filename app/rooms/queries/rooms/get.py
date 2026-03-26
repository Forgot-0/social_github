from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.rooms.dtos.rooms import RoleDTO, RoomDetailDTO, RoomMemberDTO
from app.rooms.exceptions import RoomNotFoundException
from app.rooms.repositories.rooms import RoomRepository


@dataclass(frozen=True)
class GetRoomQuery(BaseQuery):
    slug: str


@dataclass(frozen=True)
class GetRoomQueryHandler(BaseQueryHandler[GetRoomQuery, RoomDetailDTO]):
    room_repository: RoomRepository

    async def handle(self, query: GetRoomQuery) -> RoomDetailDTO:
        room = await self.room_repository.get_by_slug(query.slug)
        if room is None:
            raise RoomNotFoundException(slug=query.slug)

        return RoomDetailDTO.model_validate(**room.to_dict())
