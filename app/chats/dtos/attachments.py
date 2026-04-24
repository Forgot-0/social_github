from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.chats.models.attachment import AttachmentType


class AttachmentDTO(BaseModel):
    id: UUID
    message_id: int
    chat_id: int
    uploader_id: int
    attachment_type: AttachmentType
    mime_type: str
    original_filename: str
    file_size: int

    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UploadSlotDTO(BaseModel):
    upload_token: UUID
    upload_url: str
    attachment_type: AttachmentType
    expires_in: int


class AttachmentDownloadUrlDTO(BaseModel):
    attachment_id: UUID
    url: str
    expires_in: int
