from datetime import datetime

from pydantic import BaseModel

from app.chats.dtos.members import MemberInfoDTO, MemberPresenceDTO
from app.chats.models.chat import ChatType


class ChatDTO(BaseModel):
    id: int
    user_id_1: int
    user_id_2: int
    last_message_at: datetime | None
    created_at: datetime


class ChatListItemDTO(BaseModel):
    id: int
    type: ChatType
    name: str | None
    description: str | None
    avatar_url: str | None
    is_public: bool
    created_by: int
    last_activity_at: datetime | None
    unread_count: int = 0
    member_count: int = 0


class ChatDetailDTO(BaseModel):
    id: int
    type: ChatType
    name: str | None
    description: str | None
    avatar_url: str | None
    is_public: bool
    created_by: int
    members: list[MemberInfoDTO]
    unread_count: int = 0


class ChatPresenceDTO(BaseModel):
    chat_id: int
    members: list[MemberPresenceDTO]
    online_count: int


class ChatListCursorPageDTO(BaseModel):
    items: list[ChatListItemDTO]
    next_cursor: str | None = None
    has_more: bool = False
