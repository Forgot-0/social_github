from dataclasses import dataclass, field
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.dtos.messages import MessageDTO
from app.chats.exceptions import (
    AccessDeniedChatException,
    AttachmentNotFoundException,
    NotFoundChatException,
    NotFoundMessageException,
)
from app.chats.models.message import Message, MessageType
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.slow_mode import SlowModeService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SendMessageCommand(BaseCommand):
    chat_id: UUID
    content: str | None
    reply_to_id: UUID | None = None
    message_type: MessageType = MessageType.TEXT
    upload_tokens: list[UUID] = field(default_factory=list)

    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class SendMessageCommandHandler(BaseCommandHandler[SendMessageCommand, MessageDTO]):
    session: AsyncSession
    chat_repository: ChatRepository
    access_service: ChatAccessService
    message_repository: MessageRepository
    attachment_repository: AttachmentRepository
    slow_mode_sevice: SlowModeService
    event_bus: BaseEventBus

    async def handle(self, command: SendMessageCommand) -> MessageDTO:
        chat = await self.chat_repository.get_by_id(command.chat_id, with_for_update=True)
        if chat is None:
            raise NotFoundChatException(chat_id=str(command.chat_id))

        user_id = int(command.user_jwt_data.id)
        member = await self.chat_repository.get_member_chat(
            chat_id=command.chat_id, member_id=user_id
        )

        if not await self.access_service.can_send_message(
            user_jwt_data=command.user_jwt_data,
            chat=chat,
            member=member,
        ):
            raise AccessDeniedChatException(
                chat_id=str(command.chat_id), requester_id=user_id
            )

        await self.slow_mode_sevice.is_slow(chat=chat, user_id=user_id, member=member)

        claimed = []
        if command.upload_tokens:
            claimed = await self.attachment_repository.get_by_ids(command.upload_tokens)

        if claimed and len(command.upload_tokens) != len(claimed):
            raise AttachmentNotFoundException(attachment_id="")

        if command.reply_to_id is not None:
            reply_msg = await self.message_repository.get_by_id(command.reply_to_id)
            if reply_msg is None:
                raise NotFoundMessageException(message_id=str(command.reply_to_id))

        chat.seq_counter += 1
        msg = Message.create(
            sender_id=user_id,
            chat_id=command.chat_id,
            seq=chat.seq_counter,
            content=command.content,
            reply_to_id=command.reply_to_id,
            message_type=command.message_type,
            attachments=claimed,
        )
        chat.update_last_activity(message_date=msg.created_at)

        await self.message_repository.create(msg)
        await self.session.commit()

        await self.event_bus.publish(msg.pull_events())
        logger.info(
            "Message sent",
            extra={
                "chat_id": command.chat_id,
                "message_id": msg.id,
                "author": user_id,
                "attachments": len(claimed),
                "fanout_strategy": chat.fanout_strategy.value,
            },
        )
        return MessageDTO.model_validate(msg.to_dict())
