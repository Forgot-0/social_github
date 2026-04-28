
from pydantic import BaseModel


class MemberChatDTO(BaseModel):
    user_id: int
    role_id: int
    is_muted: bool
    is_banned: bool


class MemberPresenceDTO(BaseModel):
    user_id: int
    is_online: bool


class MemeberDetailDTO(BaseModel):
    user_id: int
    role_id: int
    is_muted: bool
    is_banned: bool

    is_online: bool
    role: Role


class Role(BaseModel):
    id: int
    name: str
    level: int
    permissions: dict[str, bool]
