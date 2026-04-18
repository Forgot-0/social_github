import logging
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.config import chat_config
from app.chats.events.messages.sended import SendedMessageEvent
from app.chats.exceptions import (
    AccessDeniedChatException,
    AttachmentValidationException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.models.attachment import MessageAttachment
from app.chats.models.message import Message, MessageType
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.attachment_service import AttachmentService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SendMessageCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    content: str | None
    reply_to_id: int | None = None
    message_type: MessageType = MessageType.TEXT
    upload_tokens: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SendMessageResult:
    message_id: int
    chat_id: int
    created_at: datetime
    attachment_count: int = 0


@dataclass(frozen=True)
class SendMessageCommandHandler(BaseCommandHandler[SendMessageCommand, SendMessageResult]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    attachment_repository: AttachmentRepository
    chat_access_servise: ChatAccessService
    attachment_service: AttachmentService
    event_bus: BaseEventBus

    async def handle(self, command: SendMessageCommand) -> SendMessageResult:
        user_id = int(command.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=command.chat_id)

        member = await self.chat_repository.get_member(command.chat_id, user_id, with_role=True)
        if not member:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=user_id)

        if not self.chat_access_servise.can_update(
            user_jwt_data=command.user_jwt_data,
            memeber=member,
            must_permissions={"message:send"},
        ):
            raise AccessDeniedChatException()

        if not command.content and not command.upload_tokens:
            raise AttachmentValidationException(
                mime_type="Either content or upload_tokens must be provided"
            )

        claimed = []
        if command.upload_tokens:
            claimed = await self.attachment_service.claim_tokens_for_message(
                user_id=user_id,
                chat_id=command.chat_id,
                tokens=list(command.upload_tokens),
            )

        msg = Message.create(
            sender_id=user_id,
            chat_id=command.chat_id,
            content=command.content,
            reply_to_id=command.reply_to_id,
            message_type=command.message_type,
        )
        msg = await self.message_repository.create(msg)

        if claimed:
            attachments = [
                MessageAttachment(
                    id=uuid4(),
                    message_id=msg.id,
                    chat_id=command.chat_id,
                    uploader_id=user_id,
                    attachment_type=att.attachment_type,
                    s3_key=att.s3_key,
                    bucket=chat_config.ATTACHMENT_BUCKET,
                    mime_type=att.mime_type,
                    original_filename=att.original_filename,
                    file_size=att.file_size,
                )
                for att in claimed
            ]
            await self.attachment_repository.create_bulk(attachments)

        chat.update_last_activity(message_id=msg.id, message_date=msg.created_at)
        await self.session.commit()

        await self.event_bus.publish([
            SendedMessageEvent(
                chat_id=chat.id,
                sender_id=user_id,
                message_id=msg.id,
                content=msg.content,
                send_at=msg.created_at,
                is_edited=msg.is_edited,
                message_type=msg.type,
                attachment_count=len(claimed),
            )
        ])

        logger.info(
            "Message sent",
            extra={
                "chat_id": command.chat_id,
                "message_id": msg.id,
                "author": user_id,
                "attachments": len(claimed),
            },
        )
        return SendMessageResult(
            message_id=msg.id,
            chat_id=msg.chat_id,
            created_at=msg.created_at,
            attachment_count=len(claimed),
        )
