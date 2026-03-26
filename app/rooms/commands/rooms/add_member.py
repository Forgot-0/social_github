import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.rooms.exceptions import InsufficientRoomPermissionException, RoomNotFoundException, RoomRoleNotFoundException
from app.rooms.repositories.roles import RoomRoleRepository
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.access import RoomAccessService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddMemberRoomCommand(BaseCommand):
    slug: str
    member_id: int
    member_username: str
    role_id: int
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class AddMemberRoomCommandHandler(BaseCommandHandler[AddMemberRoomCommand, None]):
    session: AsyncSession
    room_repository: RoomRepository
    room_role_repository: RoomRoleRepository
    room_access_service: RoomAccessService

    async def handle(self, command: AddMemberRoomCommand) -> None:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        role = await self.room_role_repository.get_by_id(command.role_id)
        if role is None:
            raise RoomRoleNotFoundException(role_id=command.role_id)

        if not self.room_access_service.can_member(
            user_jwt_data=command.user_jwt_data,
            room=room,
            must_permissions={"manage_roles"},
            role=role
        ): raise InsufficientRoomPermissionException(required="manage_roles")

        room.add_memeber(
            member_id=command.member_id,
            username=command.member_username,
            role_id=command.role_id
        )

        await self.session.commit()
        logger.info(
            "Add member to room", 
            extra={
                "member_id": command.member_id,
                "username": command.member_username,
                "room_slug": command.slug,
                "added_by": command.user_jwt_data.id
            }
        )
