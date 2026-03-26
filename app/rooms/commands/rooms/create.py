import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.rooms.exceptions import RoomAlreadyExistsException
from app.rooms.models.permissions import OWNER_ROLE
from app.rooms.models.rooms import Room
from app.rooms.repositories.roles import RoomRoleRepository
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.livekit_service import LiveKitService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateRoomCommand(BaseCommand):
    slug: str
    name: str
    description: str | None
    is_public: bool
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class CreateRoomCommandHandler(BaseCommandHandler[CreateRoomCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    role_repository: RoomRoleRepository
    livekit_service: LiveKitService

    async def handle(self, command: CreateRoomCommand) -> None:
        if await self.room_repository.exists(command.slug):
            raise RoomAlreadyExistsException(slug=command.slug)

        room = Room.create(
            slug=command.slug,
            name=command.name,
            description=command.description,
            is_public=command.is_public,
            created_by=int(command.user_jwt_data.id),
        )

        room.add_memeber(
            member_id=int(command.user_jwt_data.id),
            username=command.user_jwt_data.username,
            role_id=OWNER_ROLE.id
        )

        await self.room_repository.create(room)

        await self.session.commit()
        await self.room_repository.invalidate_cache()

        await self.livekit_service.create_room(
            slug=command.slug,
            metadata=command.name,
        )

        logger.info(
            "Room created",
            extra={
                "slug": command.slug,
                "created_by": command.user_jwt_data.id,
            },
        )
