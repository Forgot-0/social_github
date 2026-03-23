from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateChatCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True)
class UpdateChatCommandHandler(BaseCommandHandler[UpdateChatCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    chat_access_servise: ChatAccessService

    async def handle(self, command: UpdateChatCommand) -> None:
        user_id = int(command.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(command.chat_id)
        if not chat:
            raise NotFoundChatException(chat_id=command.chat_id)

        member = await self.chat_repository.get_member(command.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=user_id)

        if not self.chat_access_servise.can_update(
            user_jwt_data=command.user_jwt_data,
            memeber=member,
            must_permissions={"chat:update"}
        ): raise AccessDeniedChatException()

        if command.name is not None:
            chat.name = command.name
        if command.description is not None:
            chat.description = command.description
        if command.avatar_url is not None:
            chat.avatar_url = command.avatar_url

        await self.session.commit()
        logger.info("Chat updated", extra={"chat_id": command.chat_id, "by": user_id})

