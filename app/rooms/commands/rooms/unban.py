import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.rooms.exceptions import (
    InsufficientRoomPermissionException,
    RoomNotFoundException,
)
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.access import RoomAccessService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnbanMemberCommand(BaseCommand):
    slug: str
    target_user_id: int
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class UnbanMemberCommandHandler(BaseCommandHandler[UnbanMemberCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    room_access_service: RoomAccessService

    async def handle(self, command: UnbanMemberCommand) -> None:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        if not self.room_access_service.can_update(
            user_jwt_data=command.user_jwt_data,
            room=room,
            must_permissions={"ban"},
        ):
            raise InsufficientRoomPermissionException(required="ban")

        ban = await self.room_repository.get_ban(command.slug, command.target_user_id)
        if ban is not None:
            await self.room_repository.delete_ban(ban)
            await self.session.commit()

        logger.info(
            "Member unbanned from room",
            extra={
                "slug": command.slug,
                "target_user_id": command.target_user_id,
                "unbanned_by": command.user_jwt_data.id,
            },
        )
