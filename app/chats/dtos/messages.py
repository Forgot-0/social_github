from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.chats.dtos.attachments import AttachmentDTO


class MessageDTO(BaseModel):
    id: UUID
    chat_id: UUID
    seq: int
    author_id: int | None
    content: str | None
    reply_to_id: UUID | None
    forwarded_from_chat_id: UUID | None
    forwarded_from_message_id: UUID | None
    is_edited: bool
    created_at: datetime

    attachments: list[AttachmentDTO] = Field(default_factory=list)
    reply_to: Optional["MessageDTO"] = Field(default=None)


class ReadDetail(BaseModel):
    last_read_message_seq: int
    last_read_at: datetime


