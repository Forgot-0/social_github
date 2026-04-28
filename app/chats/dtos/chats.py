from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.chats.dtos.members import MemberChatDTO
from app.chats.dtos.messages import ReadDetail
from app.chats.models.chat import ChatType


class ChatDTO(BaseModel):
    id: UUID
    seq_counter: int
    last_activity_at: datetime | None

    type: ChatType
    name: str | None
    description: str | None
    avatar_s3_key: str | None

    is_public: bool
    created_by: int

    member_count: int
    unread_count: int
    me: MemberChatDTO
    last_read: ReadDetail | None


class ChatDetaiDTO(BaseModel):
    id: UUID
    seq_counter: int
    last_activity_at: datetime | None

    type: ChatType
    name: str | None
    description: str | None
    avatar_s3_key: str | None

    is_public: bool
    created_by: int

    member_count: int
    members: list[MemberChatDTO]


class ListChats(BaseModel):
    has_next: bool
    chats: list[ChatDTO]
    next_date: datetime | None
    next_chat_id: UUID

