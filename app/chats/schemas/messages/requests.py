from pydantic import BaseModel, Field

from app.chats.models.message import MessageType


class SendMessageRequest(BaseModel):
    content: str = Field(..., max_length=4096)
    reply_to_id: int | None = Field(default=None)
    message_type: MessageType = MessageType.TEXT


class EditMessageRequest(BaseModel):
    content: str = Field(..., max_length=4096)


class MarkAsReadRequest(BaseModel):
    message_id: int


class GetMessagesRequest(BaseModel):
    limit: int = Field(default=30, ge=30, le=100)
    before_id: int | None = Field(default=None)
