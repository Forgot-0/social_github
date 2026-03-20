from datetime import datetime

from pydantic import BaseModel

from app.chats.models.chat import ChatType


class ChatResponse(BaseModel):
    id: int
    type: ChatType
    name: str | None
    description: str | None
    avatar_url: str | None
    is_public: bool
    created_by: int
    created_at: datetime
    last_activity_at: datetime | None

    unread_count: int | None = None



class ChatListResponce(BaseModel):
    id: int
    type: ChatType
    name: str | None
    avatar_url: str | None
    last_activity_at: datetime | None
    unread_count: int = 0
