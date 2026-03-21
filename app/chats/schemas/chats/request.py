from pydantic import BaseModel, Field, field_validator

from app.chats.models.chat import ChatType
from app.chats.models.chat_members import MemberRole


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
    role: MemberRole = MemberRole.MEMBER


class ChangeMemberRoleRequest(BaseModel):
    role: MemberRole


class GetChatsRequest(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class UpdateChatRequest(BaseModel):
    name: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=1024)
    avatar_url: str | None = None


class ChangeRoleRequest(BaseModel):
    role: MemberRole


class BanRequest(BaseModel):
    ban: bool = True


