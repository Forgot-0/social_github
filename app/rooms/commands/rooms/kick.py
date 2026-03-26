import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.rooms.exceptions import (
    CannotKickOwnerException,
    InsufficientRoomPermissionException,
    NotRoomMemberException,
    RoomNotFoundException,
)
from app.rooms.models.permissions import OWNER_ROLE
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.access import RoomAccessService
from app.rooms.services.livekit_service import LiveKitService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KickMemberCommand(BaseCommand):
    slug: str
    target_user_id: int
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class KickMemberCommandHandler(BaseCommandHandler[KickMemberCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    room_access_service: RoomAccessService
    livekit_service: LiveKitService

    async def handle(self, command: KickMemberCommand) -> None:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        target = room.get_member_by_id(command.target_user_id)
        if target is None:
            raise NotRoomMemberException(user_id=command.target_user_id, slug=command.slug)

        if target.user_id == room.created_by:
            raise CannotKickOwnerException()

        if not self.room_access_service.can_manage_member(
            user_jwt_data=command.user_jwt_data,
            room=room,
            must_permissions={"kick"},
            target_role=target.role,
        ):
            raise InsufficientRoomPermissionException(required="kick")

        await self.session.delete(target)
        await self.session.commit()

        await self.livekit_service.remove_participant(
            slug=command.slug,
            identity=str(command.target_user_id),
        )

        logger.info(
            "Member kicked from room",
            extra={
                "slug": command.slug,
                "target_user_id": command.target_user_id,
                "kicked_by": command.user_jwt_data.id,
            },
        )
