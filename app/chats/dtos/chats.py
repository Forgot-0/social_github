from pydantic import BaseModel

from app.chats.dtos.members import MemberInfoDTO
from app.chats.models.chat import ChatType


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
