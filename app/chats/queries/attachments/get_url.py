from dataclasses import dataclass
from uuid import UUID

from app.chats.dtos.attachments import AttachmentDownloadUrlDTO
from app.chats.exceptions import (
    AttachmentNotFoundException,
    NotChatMemberException,
)
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.services.attachment_service import _DOWNLOAD_URL_TTL, AttachmentService
from app.core.queries import BaseQuery, BaseQueryHandler
from app.core.services.auth.dto import UserJWTData


@dataclass(frozen=True)
class GetAttachmentDownloadUrlQuery(BaseQuery):
    user_jwt_data: UserJWTData
    chat_id: int
    message_id: int
    attachment_id: UUID


@dataclass(frozen=True)
class GetAttachmentDownloadUrlQueryHandler(
    BaseQueryHandler[GetAttachmentDownloadUrlQuery, AttachmentDownloadUrlDTO]
):
    chat_repository: ChatRepository
    attachment_repository: AttachmentRepository
    attachment_service: AttachmentService

    async def handle(self, query: GetAttachmentDownloadUrlQuery) -> AttachmentDownloadUrlDTO:
        user_id = int(query.user_jwt_data.id)

        member = await self.chat_repository.get_member(query.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=query.chat_id, user_id=user_id)

        attachment = await self.attachment_repository.get_by_id(query.attachment_id)
        if (
            attachment is None
            or attachment.message_id != query.message_id
            or attachment.chat_id != query.chat_id
        ):
            raise AttachmentNotFoundException(attachment_id=str(query.attachment_id))

        url = await self.attachment_service.get_download_url(
            attachment_id=str(query.attachment_id),
            s3_key=attachment.s3_key,
        )

        return AttachmentDownloadUrlDTO(
            attachment_id=query.attachment_id,
            url=url,
            expires_in=_DOWNLOAD_URL_TTL,
        )
