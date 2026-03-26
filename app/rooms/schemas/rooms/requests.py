from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=512)
    is_public: bool = True


class UpdateRoomRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=512)
    is_public: bool | None = None


class AddMemberRequest(BaseModel):
    user_id: int
    username: str = Field(min_length=1, max_length=64)
    role_id: int


class BanMemberRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=256)


class MuteMemberRequest(BaseModel):
    is_muted: bool
