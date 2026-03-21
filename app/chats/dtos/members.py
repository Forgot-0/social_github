
from pydantic import BaseModel

from app.chats.models.chat_members import MemberRole


class MemberInfoDTO(BaseModel):
    user_id: int
    role: MemberRole
    is_muted: bool


class MemberPresenceDTO(BaseModel):
    user_id: int
    is_online: bool
