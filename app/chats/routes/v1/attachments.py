from __future__ import annotations

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status

from app.chats.commands.attachments.request_upload import (
    RequestAttachmentUploadCommand,
    RequestAttachmentUploadCommandHandler,
    UploadRequest,
)
from app.chats.commands.attachments.success import SuccessUploadAttachmentsCommand, SuccessUploadAttachmentsCommandHandler
from app.chats.dtos.attachments import AttachmentDownloadUrlDTO, UploadSlotDTO
from app.chats.queries.attachments.get_url import GetAttachmentDownloadUrlQuery, GetAttachmentDownloadUrlQueryHandler
from app.chats.schemas.rest import ConfirmAttachmentUploadRequest, RequestAttachmentUploadRequest
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter()


@router.post("/attachments/upload-requests", response_model=list[UploadSlotDTO], status_code=status.HTTP_201_CREATED)
@inject
async def request_attachment_upload(
    chat_id: UUID,
    payload: RequestAttachmentUploadRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[RequestAttachmentUploadCommandHandler],
) -> list[UploadSlotDTO]:
    return await handler.handle(
        RequestAttachmentUploadCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            uploads=[
                UploadRequest(filename=item.filename, mime_type=item.mime_type, file_size=item.file_size)
                for item in payload.uploads
            ],
        )
    )


@router.post("/attachments/upload-requests:confirm", status_code=status.HTTP_202_ACCEPTED)
@inject
async def confirm_attachment_upload(
    chat_id: UUID,
    payload: ConfirmAttachmentUploadRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[SuccessUploadAttachmentsCommandHandler],
) -> None:
    await handler.handle(
        SuccessUploadAttachmentsCommand(
            chat_id=chat_id,
            upload_tokens=[str(token) for token in payload.upload_tokens],
            user_jwt_data=user_jwt_data,
        )
    )


@router.get("/messages/{message_id}/attachments/{attachment_id}/download-url", response_model=AttachmentDownloadUrlDTO)
@inject
async def get_attachment_download_url(
    chat_id: UUID,
    message_id: UUID,
    attachment_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[GetAttachmentDownloadUrlQueryHandler],
) -> AttachmentDownloadUrlDTO:
    return await handler.handle(
        GetAttachmentDownloadUrlQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
            attachment_id=attachment_id,
        )
    )
