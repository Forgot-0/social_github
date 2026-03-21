from dataclasses import dataclass
import logging
 
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundMessageException,
)
from app.chats.models.permission import ROLE_PERMISSIONS, Permission
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
 
logger = logging.getLogger(__name__)
 
 
@dataclass(frozen=True)
class DeleteMessageCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    message_id: int
 
 
@dataclass(frozen=True)
class DeleteMessageCommandHandler(BaseCommandHandler[DeleteMessageCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    event_bus: BaseEventBus

    async def handle(self, command: DeleteMessageCommand) -> None:
        user_id = int(command.user_jwt_data.id)

        message = await self.message_repository.get_by_id(command.message_id)
        if not message or message.chat_id != command.chat_id:
            raise NotFoundMessageException(message_id=command.message_id)

        member = await self.chat_repository.get_member(command.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=user_id)

        perms = ROLE_PERMISSIONS.get(member.role, set())

        can_delete = (
            (message.author_id == user_id) or
            (Permission.DELETE_ANY_MSG in perms)
        )
        if not can_delete:
            raise AccessDeniedChatException()

        message.delete(deleted_by=user_id)
        await self.session.commit()
        await self.event_bus.publish(message.pull_events())

        logger.info(
            "Message deleted",
            extra={"chat_id": command.chat_id, "message_id": command.message_id, "by": user_id},
        )
