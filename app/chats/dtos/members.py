
from pydantic import BaseModel


class MemberInfoDTO(BaseModel):
    user_id: int
    role_id: int
    is_muted: bool


class MemberPresenceDTO(BaseModel):
    user_id: int
    is_online: bool
