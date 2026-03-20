from pydantic import BaseModel, Field, field_validator

from app.chats.models.chat import ChatType


class ChatBase(BaseModel):
    name: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=1024)


class ChatRequest(ChatBase):
    chat_type: ChatType

    is_public: bool = Field(default=True)
    member_ids: list[int] = Field(default_factory=list, max_length=1000)


class ChatUpdate(ChatBase):
    avatar: str | None = Field(default=None)


