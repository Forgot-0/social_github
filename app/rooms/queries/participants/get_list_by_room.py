from dataclasses import dataclass

from app.core.queries import BaseQuery, BaseQueryHandler
from app.rooms.dtos.livekit import LiveKitParticipantsDTO
from app.rooms.exceptions import RoomNotFoundException
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.livekit_service import LiveKitService


@dataclass(frozen=True)
class GetParticipantsQuery(BaseQuery):
    slug: str


@dataclass(frozen=True)
class GetParticipantsQueryHandler(BaseQueryHandler[GetParticipantsQuery, list[LiveKitParticipantsDTO]]):
    room_repository: RoomRepository
    livekit_service: LiveKitService

    async def handle(self, query: GetParticipantsQuery) -> list[LiveKitParticipantsDTO]:
        room = await self.room_repository.get_by_slug(query.slug)
        if room is None:
            raise RoomNotFoundException(slug=query.slug)

        return await self.livekit_service.list_participants(query.slug)
