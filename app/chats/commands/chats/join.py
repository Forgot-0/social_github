import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    AlreadyMemberException,
    NotFoundChatException,
)
from app.chats.models.chat import ChatType
from app.chats.repositories.chat import ChatRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JoinChatCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: UUID


@dataclass(frozen=True)
class JoinChatCommandHandler(BaseCommandHandler[JoinChatCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    event_bus: BaseEventBus

    async def handle(self, command: JoinChatCommand) -> None:
        user_id = int(command.user_jwt_data.id)
        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=str(command.chat_id))

        if chat.type == ChatType.DIRECT or not chat.is_public:
            raise AccessDeniedChatException(chat_id=str(command.chat_id), requester_id=user_id)

        existing = await self.chat_repository.get_member_chat(command.chat_id, user_id, with_role=False)
        if existing is not None and not existing.is_banned:
            raise AlreadyMemberException(user_id=user_id, chat_id=str(command.chat_id))

        role_id = 6 if chat.type == ChatType.CHANNEL else 5
        if existing is not None and existing.is_banned:
            existing.is_banned = False
            existing.role_id = role_id
            chat.member_count += 1
        else:
            chat.add_member(user_id, role_id=role_id)

        await self.session.commit()
        await self.event_bus.publish(chat.pull_events())
        logger.info("User joined public chat", extra={"chat_id": command.chat_id, "user_id": user_id})
