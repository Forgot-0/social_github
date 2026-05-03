import logging
from dataclasses import dataclass
import re
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.config import chat_config
from app.chats.dtos.attachments import UploadSlotDTO
from app.chats.exceptions import (
    AccessDeniedChatException,
    AttachmentLimitExceededException,
    AttachmentValidationException,
    EmptyAttachmentUploadRequestException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.models.attachment import AttachmentType, MessageAttachment
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.services.storage.service import StorageService


logger = logging.getLogger(__name__)
clean_filename = re.compile(r"[^\w.\-]")

@dataclass(frozen=True)
class UploadRequest:
    filename: str
    mime_type: str
    file_size: int


@dataclass(frozen=True)
class RequestAttachmentUploadCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: UUID
    uploads: list[UploadRequest]


@dataclass(frozen=True)
class RequestAttachmentUploadCommandHandler(BaseCommandHandler[RequestAttachmentUploadCommand, list[UploadSlotDTO]]):
    session: AsyncSession
    chat_repository: ChatRepository
    chat_access_service: ChatAccessService
    attachment_repository: AttachmentRepository
    storage_service: StorageService

    async def handle(self, command: RequestAttachmentUploadCommand) -> list[UploadSlotDTO]:
        user_id = int(command.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=str(command.chat_id))

        member = await self.chat_repository.get_member_chat(
            command.chat_id, user_id
        )
        if member is None:
            raise NotChatMemberException(chat_id=str(command.chat_id), user_id=user_id)

        if not await self.chat_access_service.can_send_message(
            user_jwt_data=command.user_jwt_data,
            chat=chat,
            member=member,
        ):
            raise AccessDeniedChatException(chat_id=str(command.chat_id), requester_id=user_id)

        if len(command.uploads) == 0:
            raise EmptyAttachmentUploadRequestException()

        media_count = 0
        file_count = 0
        att_types: list[AttachmentType] = []
 
        for req in command.uploads:
            if req.mime_type not in chat_config.ALL_ALLOWED_MIMES:
                raise AttachmentValidationException(mime_type=req.mime_type)
 
            if req.mime_type in chat_config.ALLOWED_IMAGE_MIMES or req.mime_type in chat_config.ALLOWED_VIDEO_MIMES:
                att_type = (
                    AttachmentType.IMAGE
                    if req.mime_type in chat_config.ALLOWED_IMAGE_MIMES
                    else AttachmentType.VIDEO
                )
                if req.file_size > chat_config.MAX_MEDIA_SIZE:
                    raise AttachmentValidationException(mime_type=req.mime_type)
                media_count += 1
            else:
                att_type = AttachmentType.FILE
                if req.file_size > chat_config.MAX_FILE_SIZE:
                    raise AttachmentValidationException(mime_type=req.mime_type)
                file_count += 1
 
            att_types.append(att_type)

        if media_count > chat_config.MAX_MEDIA_PER_MESSAGE:
            raise AttachmentLimitExceededException(count=media_count)
 
        if file_count > chat_config.MAX_FILES_PER_MESSAGE:
            raise AttachmentLimitExceededException(count=file_count)

        slots = []

        for slot, att_type in zip(command.uploads, att_types):
            new_file_name = clean_filename.sub("_", slot.filename.strip())[:200]
            s3_key = f"chats/{command.chat_id}/{uuid4()}/{new_file_name}"
 
            upload_url = await self.storage_service.upload_put_url(
                bucket_name=chat_config.ATTACHMENT_BUCKET,
                file_key=s3_key,
                expires=chat_config.ATTACHMENT_UPLOAD_TOKEN_TTL,
            )
 
            attachment = MessageAttachment.create(
                chat_id=command.chat_id,
                uploader_id=user_id,
                attachment_type=att_type,
                s3_key=s3_key,
                mime_type=slot.mime_type,
                original_filename=slot.filename,
                size=slot.file_size,
            )
            await self.attachment_repository.create(attachment)
 
            slots.append(
                UploadSlotDTO(
                    upload_token=attachment.id,
                    upload_url=upload_url,
                    attachment_type=att_type,
                    expires_in=chat_config.ATTACHMENT_UPLOAD_TOKEN_TTL,
                )
            )

        await self.session.commit()
        logger.info(
            "Upload slots created",
            extra={"chat_id": command.chat_id, "user_id": user_id, "count": len(slots)},
        )
        return slots
