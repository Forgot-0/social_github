from dataclasses import dataclass
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.events.messages.sended import SendedMessageEvent
from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.models.message import Message, MessageType
from app.chats.models.permission import ROLE_PERMISSIONS, Permission
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData



logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SendMessageCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    content: str
    reply_to_id: int | None = None
    message_type: MessageType = MessageType.TEXT


@dataclass(frozen=True)
class SendMessageResult:
    message_id: int
    chat_id: int
    created_at: datetime


@dataclass(frozen=True)
class SendMessageCommandHandler(BaseCommandHandler[SendMessageCommand, SendMessageResult]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    event_bus: BaseEventBus

    async def handle(self, command: SendMessageCommand) -> SendMessageResult:
        user_id = int(command.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=command.chat_id)

        member = await self.chat_repository.get_member(command.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=user_id)

        if Permission.SEND_MESSAGES not in ROLE_PERMISSIONS.get(member.role, set()):
            raise AccessDeniedChatException()

        msg = Message.create(
            chat_id=command.chat_id,
            sender_id=user_id,
            message_type=command.message_type,
            content=command.content,
            reply_to_id=command.reply_to_id,
        )
        msg = await self.message_repository.create(msg)

        chat.update_last_activity(message_id=msg.id, message_date=msg.created_at)

        await self.session.commit()
        await self.event_bus.publish(
            [
                SendedMessageEvent(
                    chat_id=chat.id,
                    sender_id=user_id,
                    message_id=msg.id,
                    content=msg.content,
                    send_at=msg.created_at,
                    is_edited=msg.is_edited,
                    message_type=msg.type
                )
            ]
        )
        logger.info(
            "Message sent",
            extra={"chat_id": command.chat_id, "message_id": msg.id, "author": user_id},
        )
        return SendMessageResult(
            message_id=msg.id,
            chat_id=msg.chat_id,
            created_at=msg.created_at,
        )
