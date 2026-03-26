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
    UserBannedException,
)
from app.rooms.models.permissions import OWNER_ROLE
from app.rooms.models.rooms import RoomBan
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.access import RoomAccessService
from app.rooms.services.livekit_service import LiveKitService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BanMemberCommand(BaseCommand):
    slug: str
    target_user_id: int
    reason: str | None
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class BanMemberCommandHandler(BaseCommandHandler[BanMemberCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    room_access_service: RoomAccessService
    livekit_service: LiveKitService

    async def handle(self, command: BanMemberCommand) -> None:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        existing_ban = await self.room_repository.get_ban(command.slug, command.target_user_id)
        if existing_ban is not None:
            raise UserBannedException(user_id=command.target_user_id, slug=command.slug)

        target = room.get_member_by_id(command.target_user_id)
        if target is None:
            raise NotRoomMemberException(user_id=command.target_user_id, slug=command.slug)

        if target.user_id == room.created_by:
            raise CannotKickOwnerException()

        if not self.room_access_service.can_manage_member(
            user_jwt_data=command.user_jwt_data,
            room=room,
            must_permissions={"ban"},
            target_role=target.role,
        ):
            raise InsufficientRoomPermissionException(required="ban")

        await self.session.delete(target)

        ban = RoomBan(
            room_slug=command.slug,
            user_id=command.target_user_id,
            reason=command.reason,
            banned_by=int(command.user_jwt_data.id),
        )
        self.session.add(ban)
        await self.session.commit()

        await self.livekit_service.remove_participant(
            slug=command.slug,
            identity=str(command.target_user_id),
        )

        logger.info(
            "Member banned from room",
            extra={
                "slug": command.slug,
                "target_user_id": command.target_user_id,
                "banned_by": command.user_jwt_data.id,
                "reason": command.reason,
            },
        )
