from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    name: str
    description: str | None = Field(default=None)
    is_public: bool


class UpdateRoomRequest(BaseModel):
    name: str | None
    description: str | None
    is_public: bool | None

