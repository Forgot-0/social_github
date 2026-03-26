import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.rooms.exceptions import InsufficientRoomPermissionException, RoomNotFoundException
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.access import RoomAccessService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateRoomCommand(BaseCommand):
    slug: str
    name: str | None
    description: str | None
    is_public: bool | None
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class UpdateRoomCommandHandler(BaseCommandHandler[UpdateRoomCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    room_access_service: RoomAccessService

    async def handle(self, command: UpdateRoomCommand) -> None:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        if not self.room_access_service.can_update(
            user_jwt_data=command.user_jwt_data,
            room=room,
            must_permissions={"manage_channels"}
        ): raise InsufficientRoomPermissionException(required="manage_channels")

        if command.name is not None:
            room.name = command.name
        if command.description is not None:
            room.description = command.description
        if command.is_public is not None:
            room.is_public = command.is_public

        await self.session.commit()
        await self.room_repository.invalidate_cache()

        logger.info(
            "Room updated",
            extra={"slug": command.slug, "updated_by": command.user_jwt_data.id},
        )
