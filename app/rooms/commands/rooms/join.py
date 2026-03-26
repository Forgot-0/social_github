import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.rooms.config import room_config
from app.rooms.dtos.livekit import JoinTokenDTO
from app.rooms.exceptions import (
    NotRoomMemberException,
    RoomNotFoundException,
    UserBannedException,
)
from app.rooms.models.permissions import MEMBER_ROLE
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.livekit_service import LiveKitService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JoinRoomCommand(BaseCommand):
    slug: str
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class JoinRoomCommandHandler(BaseCommandHandler[JoinRoomCommand, JoinTokenDTO]):
    session: AsyncSession
    room_repository: RoomRepository
    livekit_service: LiveKitService

    async def handle(self, command: JoinRoomCommand) -> JoinTokenDTO:
        room = await self.room_repository.get_by_slug(command.slug)
        if room is None:
            raise RoomNotFoundException(slug=command.slug)

        user_id = int(command.user_jwt_data.id)

        ban = await self.room_repository.get_ban(command.slug, user_id)
        if ban is not None:
            raise UserBannedException(user_id=user_id, slug=command.slug)

        member = room.get_member_by_id(user_id)

        if member is None:
            if not room.is_public:
                raise NotRoomMemberException(user_id=user_id, slug=command.slug)

            member = room.add_memeber(
                member_id=user_id,
                username=command.user_jwt_data.username,
                role_id=MEMBER_ROLE.id,
            )
            await self.session.flush()

        perms = member.effective_permissions()
        can_connect = perms.get("connect_voice", True)
        can_publish = can_connect and perms.get("speak", True) and not member.is_muted
        can_publish_data = perms.get("send_message", True)

        token = self.livekit_service.generate_join_token(
            slug=command.slug,
            user_id=str(user_id),
            username=command.user_jwt_data.username,
            can_publish=can_publish,
            can_subscribe=can_connect,
            can_publish_data=can_publish_data,
        )

        await self.session.commit()

        logger.info(
            "User joined room",
            extra={"slug": command.slug, "user_id": user_id},
        )

        return JoinTokenDTO(
            token=token,
            slug=command.slug,
            livekit_url=room_config.LIVEKIT_URL,
        )
