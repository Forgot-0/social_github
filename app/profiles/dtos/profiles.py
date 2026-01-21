from pydantic import BaseModel



class ProfileDTO(BaseModel):
    id: int
    user_id: int
    avatar_url: str | None
    display_name: str | None
    bio: str | None
    skills: set[str]


class AvatarPresignResponse(BaseModel):
    url: str
    fields: dict[str, str]
    key_base: str

