from pydantic import BaseModel, Field


class Role(BaseModel):
    id: int
    name: str
    level: int
    permissions: dict[str, bool] = Field(default_factory=dict)


class MemberChatDTO(BaseModel):
    user_id: int
    role_id: int
    is_muted: bool
    is_banned: bool
    permissions_overrides: dict[str, bool] = Field(default_factory=dict)


class MemberPresenceDTO(BaseModel):
    user_id: int
    is_online: bool


class MemeberDetailDTO(BaseModel):
    user_id: int
    role_id: int
    is_muted: bool
    is_banned: bool
    permissions_overrides: dict[str, bool] = Field(default_factory=dict)

    is_online: bool
    role: Role


class ListMembers(BaseModel):
    members: list[MemberChatDTO]
    has_next: bool
    next_user_id: int | None = None
    presence: list[MemberPresenceDTO] = Field(default_factory=list)
