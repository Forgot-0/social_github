from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.chats.models.message import MessageType

from app.chats.dtos.attachments import AttachmentDTO


class MessageDTO(BaseModel):
    id: UUID
    chat_id: UUID
    seq: int
    author_id: int | None
    type: MessageType
    content: str | None
    reply_to_id: UUID | None
    forwarded_from_chat_id: UUID | None
    forwarded_from_message_id: UUID | None
    is_edited: bool
    created_at: datetime

    attachments: list[AttachmentDTO] = Field(default_factory=list)
    reply_to: Optional["MessageDTO"] = Field(default=None)
    forwarded_from: Optional["MessageDTO"] = Field(default=None)


class ReadDetail(BaseModel):
    last_read_message_seq: int
    last_read_at: datetime


class MessagesDTO(BaseModel):
    messages: list[MessageDTO]
    next_cursor: int | None
    has_next: bool

