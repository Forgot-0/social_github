from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.chats.models.message import MessageType


class UploadRequestItem(BaseModel):
    filename: str = Field(..., min_length=1, max_length=256)
    mime_type: str = Field(..., min_length=3, max_length=128)
    file_size: int = Field(..., gt=0, le=100 * 1024 * 1024)


class RequestAttachmentUploadRequest(BaseModel):
    uploads: list[UploadRequestItem] = Field(..., min_length=1, max_length=11)


class SendMessageRequest(BaseModel):
    content: str | None = Field(default=None, max_length=4096)
    reply_to_id: int | None = Field(default=None)
    message_type: MessageType = MessageType.TEXT
    upload_tokens: list[UUID] = Field(default_factory=list, max_length=11)

    @model_validator(mode="after")
    def validate_content_or_attachments(self) -> "SendMessageRequest":
        if not self.content and not self.upload_tokens:
            raise ValueError("Either content or upload_tokens must be provided")
        return self


class ForwardMessageRequest(BaseModel):
    source_chat_id: int
    source_message_id: int
    comment: str | None = Field(default=None, max_length=4096)


class EditMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4096)


class MarkAsReadRequest(BaseModel):
    message_id: int


class GetMessagesRequest(BaseModel):
    limit: int = Field(default=30, ge=1, le=100)
    before_id: int | None = Field(default=None)


class GetMessageReadDetailsRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    after_user_id: int | None = None
