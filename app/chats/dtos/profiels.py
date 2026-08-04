from pydantic import BaseModel, ConfigDict, Field


class ChatProfileDTO(BaseModel):
    user_id: int
    username: str | None = None
    display_name: str | None = None
    avatars: dict[str, dict[str, str]] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
