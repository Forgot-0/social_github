from dataclasses import dataclass
import logging
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.events.messages.sended import SendedMessageEvent
from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundChatException,
    NotFoundMessageException,
)
from app.chats.models.attachment import MessageAttachment
from app.chats.models.message import Message, MessageType
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.attachment_service import ATTACHMENT_BUCKET
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ForwardMessageCommand(BaseCommand):
    user_jwt_data: UserJWTData
    # Откуда берём сообщение
    source_chat_id: int
    source_message_id: int
    # Куда пересылаем
    target_chat_id: int
    # Опциональный комментарий к пересланному сообщению
    comment: str | None = None


@dataclass(frozen=True)
class ForwardMessageResult:
    message_id: int
    chat_id: int
    created_at: datetime
    attachment_count: int = 0


@dataclass(frozen=True)
class ForwardMessageCommandHandler(BaseCommandHandler[ForwardMessageCommand, ForwardMessageResult]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    attachment_repository: AttachmentRepository
    chat_access_servise: ChatAccessService
    event_bus: BaseEventBus

    async def handle(self, command: ForwardMessageCommand) -> ForwardMessageResult:
        user_id = int(command.user_jwt_data.id)

        source_member = await self.chat_repository.get_member(
            command.source_chat_id, user_id
        )
        if not source_member:
            raise NotChatMemberException(chat_id=command.source_chat_id, user_id=user_id)

        source_msg = await self.message_repository.get_by_id(command.source_message_id)
        if not source_msg or source_msg.chat_id != command.source_chat_id:
            raise NotFoundMessageException(message_id=command.source_message_id)

        target_chat = await self.chat_repository.get_by_id(command.target_chat_id)
        if not target_chat:
            raise NotFoundChatException(chat_id=command.target_chat_id)

        target_member = await self.chat_repository.get_member(
            command.target_chat_id, user_id, with_role=True
        )
        if not target_member:
            raise NotChatMemberException(chat_id=command.target_chat_id, user_id=user_id)

        if not self.chat_access_servise.can_update(
            user_jwt_data=command.user_jwt_data,
            memeber=target_member,
            must_permissions={"message:send"},
        ):
            raise AccessDeniedChatException()

        forwarded_msg = Message.create(
            sender_id=user_id,
            chat_id=command.target_chat_id,
            content=command.comment or source_msg.content,
            message_type=MessageType.TEXT,
            forwarded_from_chat_id=command.source_chat_id,
            forwarded_from_message_id=command.source_message_id,
        )
        forwarded_msg = await self.message_repository.create(forwarded_msg)

        source_attachments = await self.attachment_repository.get_by_message_id(
            command.source_message_id
        )
        new_attachments: list[MessageAttachment] = []
        for src in source_attachments:
            new_attachments.append(
                MessageAttachment(
                    id=uuid4(),
                    message_id=forwarded_msg.id,
                    chat_id=command.target_chat_id,
                    uploader_id=src.uploader_id,
                    attachment_type=src.attachment_type,
                    s3_key=src.s3_key,
                    bucket=ATTACHMENT_BUCKET,
                    mime_type=src.mime_type,
                    original_filename=src.original_filename,
                    file_size=src.file_size,
                    width=src.width,
                    height=src.height,
                    duration_seconds=src.duration_seconds,
                )
            )

        if new_attachments:
            await self.attachment_repository.create_bulk(new_attachments)

        target_chat.update_last_activity(
            message_id=forwarded_msg.id, message_date=forwarded_msg.created_at
        )
        await self.session.commit()

        await self.event_bus.publish([
            SendedMessageEvent(
                chat_id=command.target_chat_id,
                sender_id=user_id,
                message_id=forwarded_msg.id,
                content=forwarded_msg.content,
                send_at=forwarded_msg.created_at,
                is_edited=False,
                message_type=MessageType.TEXT,
                attachment_count=len(new_attachments),
                forwarded_from_chat_id=command.source_chat_id,
                forwarded_from_message_id=command.source_message_id,
            )
        ])

        logger.info(
            "Message forwarded",
            extra={
                "source_chat_id": command.source_chat_id,
                "source_message_id": command.source_message_id,
                "target_chat_id": command.target_chat_id,
                "new_message_id": forwarded_msg.id,
                "by": user_id,
                "attachments_copied": len(new_attachments),
            },
        )
        return ForwardMessageResult(
            message_id=forwarded_msg.id,
            chat_id=command.target_chat_id,
            created_at=forwarded_msg.created_at,
            attachment_count=len(new_attachments),
        )
