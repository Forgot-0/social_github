import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.exceptions import AccessDeniedException
from app.rooms.exceptions import RoomNotFoundException
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.access import RoomAccessService
from app.rooms.services.livekit_service import LiveKitService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeleteRoomCommand(BaseCommand):
    slug: str
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class DeleteRoomCommandHandler(BaseCommandHandler[DeleteRoomCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    livekit_service: LiveKitService
    room_access_service: RoomAccessService

    async def handle(self, command: DeleteRoomCommand) -> None:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        if not self.room_access_service.can_update(
            user_jwt_data=command.user_jwt_data,
            room=room,
            must_permissions={"room:delete"}
        ): raise AccessDeniedException(need_permissions={"room:delete"})

        room.soft_delete()
        await self.session.commit()
        await self.room_repository.invalidate_cache()

        await self.livekit_service.delete_room(command.slug)

        logger.info(
            "Room deleted",
            extra={"slug": command.slug, "deleted_by": command.user_jwt_data.id},
        )
