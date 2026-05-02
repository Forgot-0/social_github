from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.chats.config import chat_config
from app.chats.models.chat import ChatType
from app.chats.models.message import MessageType


class CreateChatRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    chat_type: ChatType = ChatType.DIRECT
    member_ids: list[int] = Field(default_factory=list, max_length=chat_config.MAX_BULK_ADD_MEMBERS)
    is_public: bool = False
    admin_only: bool = False
    slow_mode_seconds: int = Field(default=0, ge=0, le=chat_config.MAX_SLOW_MODE_SECONDS)
    permissions: dict[str, bool] = Field(default_factory=dict)


class UpdateChatRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    is_public: bool | None = None
    admin_only: bool | None = None
    slow_mode_seconds: int | None = Field(default=None, ge=0, le=chat_config.MAX_SLOW_MODE_SECONDS)
    permissions: dict[str, bool] | None = None


class AddMemberRequest(BaseModel):
    user_id: int = Field(gt=0)
    role_id: int = Field(default=5, gt=0)


class BulkAddMemberRequest(BaseModel):
    user_ids: list[int] = Field(min_length=1, max_length=chat_config.MAX_BULK_ADD_MEMBERS)
    role_id: int = Field(default=5, gt=0)

    @field_validator("user_ids")
    @classmethod
    def unique_user_ids(cls, value: list[int]) -> list[int]:
        return list(dict.fromkeys(int(user_id) for user_id in value))


class ChangeMemberRoleRequest(BaseModel):
    role_id: int = Field(gt=0)


class BanMemberRequest(BaseModel):
    ban: bool = True


class SendMessageRequest(BaseModel):
    content: str | None = Field(default=None, max_length=chat_config.MAX_MESSAGE_LENGTH)
    reply_to_id: UUID | None = None
    message_type: MessageType = MessageType.TEXT
    upload_tokens: list[UUID] = Field(default_factory=list)


class EditMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=chat_config.MAX_MESSAGE_LENGTH)


class ForwardMessageRequest(BaseModel):
    source_chat_id: UUID
    source_message_id: UUID
    comment: str | None = Field(default=None, max_length=chat_config.MAX_MESSAGE_LENGTH)


class MarkReadRequest(BaseModel):
    message_seq: int = Field(ge=0)


class UploadRequestItem(BaseModel):
    filename: str = Field(min_length=1, max_length=256)
    mime_type: str = Field(min_length=1, max_length=128)
    file_size: int = Field(gt=0, le=max(chat_config.MAX_FILE_SIZE, chat_config.MAX_MEDIA_SIZE))


class RequestAttachmentUploadRequest(BaseModel):
    uploads: list[UploadRequestItem] = Field(min_length=1, max_length=chat_config.MAX_MEDIA_PER_MESSAGE + chat_config.MAX_FILES_PER_MESSAGE)


class ConfirmAttachmentUploadRequest(BaseModel):
    upload_tokens: list[UUID] = Field(min_length=1, max_length=chat_config.MAX_MEDIA_PER_MESSAGE + chat_config.MAX_FILES_PER_MESSAGE)


class MuteParticipantRequest(BaseModel):
    muted: bool = True


class PresenceBatchRequest(BaseModel):
    user_ids: list[int] = Field(min_length=1, max_length=500)


class BulkResult(BaseModel):
    processed: int
