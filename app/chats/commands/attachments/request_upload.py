from dataclasses import dataclass, field
import logging

from app.chats.dtos.attachments import UploadSlotDTO
from app.chats.exceptions import (
    AccessDeniedChatException,
    AttachmentLimitExceededException,
    AttachmentValidationException,
    NotChatMemberException,
)
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.attachment_service import (
    ALLOWED_FILE_MIMES,
    ALLOWED_IMAGE_MIMES,
    ALLOWED_VIDEO_MIMES,
    MAX_FILES_PER_MESSAGE,
    MAX_MEDIA_PER_MESSAGE,
    AttachmentService,
    AttachmentType,
)
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadRequest:
    filename: str
    mime_type: str
    file_size: int


@dataclass(frozen=True)
class RequestAttachmentUploadCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    uploads: list[UploadRequest]


@dataclass(frozen=True)
class RequestAttachmentUploadCommandHandler(BaseCommandHandler[RequestAttachmentUploadCommand, list[UploadSlotDTO]]):
    chat_repository: ChatRepository
    chat_access_servise: ChatAccessService
    attachment_service: AttachmentService

    async def handle(self, command: RequestAttachmentUploadCommand) -> list[UploadSlotDTO]:
        user_id = int(command.user_jwt_data.id)

        member = await self.chat_repository.get_member(
            command.chat_id, user_id, with_role=True
        )
        if not member:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=user_id)

        if not self.chat_access_servise.can_update(
            user_jwt_data=command.user_jwt_data,
            memeber=member,
            must_permissions={"message:send"},
        ):
            raise AccessDeniedChatException()

        _validate_upload_requests(command.uploads)

        slots = []
        for req in command.uploads:
            slot = await self.attachment_service.create_upload_slot(
                chat_id=command.chat_id,
                user_id=user_id,
                filename=req.filename,
                mime_type=req.mime_type,
                file_size=req.file_size,
            )
            slots.append(
                UploadSlotDTO(
                    upload_token=slot.upload_token,
                    upload_url=slot.upload_url,
                    attachment_type=slot.attachment_type,
                    expires_in=slot.expires_in,
                )
            )

        logger.info(
            "Upload slots created",
            extra={"chat_id": command.chat_id, "user_id": user_id, "count": len(slots)},
        )
        return slots


def _validate_upload_requests(uploads: list[UploadRequest]) -> None:
    if not uploads:
        raise AttachmentValidationException(mime_type="No uploads provided")

    all_mimes = ALLOWED_IMAGE_MIMES | ALLOWED_VIDEO_MIMES | ALLOWED_FILE_MIMES
    media_count = 0
    file_count = 0

    for req in uploads:
        if req.mime_type not in all_mimes:
            raise AttachmentValidationException(mime_type=req.mime_type)

        att_type = AttachmentType.FILE
        if req.mime_type in ALLOWED_IMAGE_MIMES:
            att_type = AttachmentType.IMAGE
        elif req.mime_type in ALLOWED_VIDEO_MIMES:
            att_type = AttachmentType.VIDEO

        if att_type == AttachmentType.FILE:
            file_count += 1
        else:
            media_count += 1

    if media_count > MAX_MEDIA_PER_MESSAGE:
        raise AttachmentLimitExceededException(count=media_count)

    if file_count > MAX_FILES_PER_MESSAGE:
        raise AttachmentLimitExceededException(count=file_count)
