from dataclasses import dataclass, field
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.config import chat_config
from app.chats.dtos.messages import MessageDTO
from app.chats.exceptions import (
    AccessDeniedChatException,
    AttachmentLimitExceededException,
    AttachmentNotFoundException,
    NotFoundChatException
)
from app.chats.models.attachment import AttachmentStatus, AttachmentType
from app.chats.models.message import Message, MessageType
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.access import ChatAccessService
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
    event_bus: BaseEventBus

    async def handle(self, command: SendMessageCommand) -> MessageDTO:
        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=str(command.chat_id))

        user_id = int(command.user_jwt_data.id)
        member = await self.chat_repository.get_memebr_chat(
            chat_id=command.chat_id, member_id=user_id
        )

        if not self.access_service.can_update(
            user_jwt_data=command.user_jwt_data,
            memeber=member,
            must_permissions={"message:send"}
        ): raise AccessDeniedChatException(
            chat_id=str(command.chat_id), requester_id=user_id
        )
        claimed = []
        if command.upload_tokens:
            claimed= await self.attachment_repository.get_by_ids(
                command.upload_tokens
            )

        if claimed:
            if len(command.upload_tokens) != len(claimed):
                raise AttachmentNotFoundException(attachment_id="")

            media_count = sum(
                1 for a in claimed if a.attachment_type in (AttachmentType.IMAGE, AttachmentType.VIDEO)
            )
            file_count = sum(1 for a in claimed if a.attachment_type == AttachmentType.FILE)

            success = all(True if a.attachment_status == AttachmentStatus.SUCCESS else False for a in claimed)

            if media_count > chat_config.MAX_MEDIA_PER_MESSAGE:
                raise AttachmentLimitExceededException(count=media_count)
            if file_count > chat_config.MAX_FILES_PER_MESSAGE:
                raise AttachmentLimitExceededException(count=file_count)

            if success is False:
                raise AttachmentNotFoundException(attachment_id="")

        msg = Message.create(
            sender_id=user_id,
            chat_id=command.chat_id,
            seq=chat.seq_counter+1,
            content=command.content,
            reply_to_id=command.reply_to_id,
            message_type=command.message_type,
            attachments=claimed
        )
        chat.update_last_activity(chat.seq_counter, message_date=msg.created_at)
        chat.seq_counter += 1

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
            },
        )
        return MessageDTO.model_validate(msg.to_dict())
