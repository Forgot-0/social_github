import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.rooms.exceptions import CannotKickOwnerException, NotRoomMemberException, RoomNotFoundException
from app.rooms.models.permissions import OWNER_ROLE
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.livekit_service import LiveKitService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LeaveRoomCommand(BaseCommand):
    slug: str
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class LeaveRoomCommandHandler(BaseCommandHandler[LeaveRoomCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    livekit_service: LiveKitService

    async def handle(self, command: LeaveRoomCommand) -> None:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        user_id = int(command.user_jwt_data.id)
        member = room.get_member_by_id(user_id)
        if member is None:
            raise NotRoomMemberException(user_id=user_id, slug=command.slug)

        if member.role_id == OWNER_ROLE.id:
            raise CannotKickOwnerException()

        await self.session.delete(member)
        await self.session.commit()

        await self.livekit_service.remove_participant(
            slug=command.slug,
            identity=str(user_id),
        )

        logger.info(
            "User left room",
            extra={"slug": command.slug, "user_id": user_id},
        )
