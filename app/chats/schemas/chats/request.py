from pydantic import BaseModel, Field, field_validator

from app.chats.models.chat import ChatType


class CreateChatRequest(BaseModel):
    chat_type: ChatType
    member_ids: set[int] = Field(default_factory=set, max_length=99)
    name: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=1024)
    is_public: bool = False


class CreateChatResponse(BaseModel):
    chat_id: int


class AddMemberRequest(BaseModel):
    user_id: int
    role_id: int


class ChangeMemberRoleRequest(BaseModel):
    role_id: int


class GetChatsRequest(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class GetChatsCursorRequest(BaseModel):
    limit: int = Field(20, ge=1, le=100)
    cursor: str | None = None


class UpdateChatRequest(BaseModel):
    name: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=1024)
    avatar_url: str | None = None


class ChangeRoleRequest(BaseModel):
    role_id: int


class BanRequest(BaseModel):
    ban: bool = True


