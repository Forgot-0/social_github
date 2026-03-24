from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
)
from app.chats.keys import ChatKeys
from app.chats.models.chat import LeavedChatMemberEvent
from app.chats.repositories.chat import ChatRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.projects.models.role_permissions import ProjectRolesEnum


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LeaveChatCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int


@dataclass(frozen=True)
class LeaveChatCommandHandler(BaseCommandHandler[LeaveChatCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    event_bus: BaseEventBus

    async def handle(self, command: LeaveChatCommand) -> None:
        user_id = int(command.user_jwt_data.id)

        member = await self.chat_repository.get_member(command.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=user_id)

        if member.role_id == ProjectRolesEnum.OWNER.value.id:
            count = await self.chat_repository.get_member_count(command.chat_id)
            if count > 1:
                raise AccessDeniedChatException()

        await self.session.delete(member)
        await self.chat_repository.invalidate_cache(ChatKeys.chat_member_count(member.chat_id))
        await self.session.commit()
        await self.event_bus.publish(
            [LeavedChatMemberEvent(
                chat_id=member.chat_id,
                user_id=user_id
            )]
        )

        logger.info("User left chat", extra={"chat_id": command.chat_id, "user_id": user_id})
