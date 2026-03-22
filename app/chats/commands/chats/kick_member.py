from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.keys import ChatKeys
from app.chats.models.chat import KickedChatMemberEvent
from app.chats.models.chat_members import MemberRole
from app.chats.models.permission import ROLE_PERMISSIONS, Permission
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSEventType
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KickMemberCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    target_user_id: int


@dataclass(frozen=True)
class KickMemberCommandHandler(BaseCommandHandler[KickMemberCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    event_bus: BaseEventBus

    async def handle(self, command: KickMemberCommand) -> None:
        requester_id = int(command.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(command.chat_id)
        if not chat:
            raise NotFoundChatException(chat_id=command.chat_id)

        requester = await self.chat_repository.get_member(command.chat_id, requester_id)
        if not requester:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=requester_id)

        perms = ROLE_PERMISSIONS.get(requester.role, set())
        if Permission.REMOVE_MEMBERS not in perms:
            raise AccessDeniedChatException()

        target = await self.chat_repository.get_member(command.chat_id, command.target_user_id)
        if not target:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=command.target_user_id)

        if len(perms) <= len(ROLE_PERMISSIONS.get(target.role, set())):
            raise AccessDeniedChatException()

        await self.session.delete(target)
        await self.chat_repository.invadate_cache(ChatKeys.chat_member_count(chat.id))
        await self.session.commit()
        await self.event_bus.publish(
            [KickedChatMemberEvent(
                chat_id=command.chat_id,
                requester_id=requester_id,
                target_user_id=target.user_id
            )]
        )

        logger.info(
            "Member removed",
            extra={"chat_id": command.chat_id, "target": command.target_user_id, "by": requester_id},
        )

