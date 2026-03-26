import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.rooms.exceptions import (
    InsufficientRoomPermissionException,
    NotRoomMemberException,
    RoomNotFoundException,
)
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.access import RoomAccessService
from app.rooms.services.livekit_service import LiveKitService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MuteMemberCommand(BaseCommand):
    slug: str
    target_user_id: int
    is_muted: bool
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class MuteMemberCommandHandler(BaseCommandHandler[MuteMemberCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    room_access_service: RoomAccessService
    livekit_service: LiveKitService

    async def handle(self, command: MuteMemberCommand) -> None:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        target = room.get_member_by_id(command.target_user_id)
        if target is None:
            raise NotRoomMemberException(user_id=command.target_user_id, slug=command.slug)

        caller_id = int(command.user_jwt_data.id)
        if caller_id != command.target_user_id:
            if not self.room_access_service.can_manage_member(
                user_jwt_data=command.user_jwt_data,
                room=room,
                must_permissions={"mute"},
                target_role=target.role,
            ):
                raise InsufficientRoomPermissionException(required="mute")

        target.is_muted = command.is_muted
        await self.session.commit()

        perms = target.effective_permissions()
        can_speak = perms.get("speak", True) and not command.is_muted
        await self.livekit_service.set_participant_permissions(
            slug=command.slug,
            identity=str(command.target_user_id),
            can_publish=can_speak,
            can_subscribe=perms.get("connect_voice", True),
            can_publish_data=perms.get("send_message", True),
        )

        action = "muted" if command.is_muted else "unmuted"
        logger.info(
            "Member %s in room",
            action,
            extra={
                "slug": command.slug,
                "target_user_id": command.target_user_id,
                "by": command.user_jwt_data.id,
            },
        )
