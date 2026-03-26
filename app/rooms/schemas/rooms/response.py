
from pydantic import BaseModel, Field


class CreateRoomResponse(BaseModel):
    name: str
    slug: str
    description: str | None = Field(default=None)
    is_public: bool
