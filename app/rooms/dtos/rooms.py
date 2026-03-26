from pydantic import BaseModel


class RoleDTO(BaseModel):
    id: int
    name: str
    level: int
    permissions: dict[str, bool]


class RoomMemberDTO(BaseModel):
    id: int
    user_id: int
    username: str
    role: RoleDTO
    is_muted: bool


class RoomDTO(BaseModel):
    slug: str
    name: str
    description: str | None
    is_public: bool
    created_by: int
    member_count: int = 0


class RoomDetailDTO(RoomDTO):
    members: list[RoomMemberDTO] = []


class JoinTokenDTO(BaseModel):
    token: str
    slug: str
    livekit_url: str


class LiveParticipantDTO(BaseModel):
    identity: str
    name: str
    state: int
    joined_at: int
