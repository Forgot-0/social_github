from datetime import date
from pydantic import BaseModel

from app.profiles.dtos.contacts import ContactDTO


class ProfileDTO(BaseModel):
    id: int
    user_id: int
    avatars: dict[int, dict[str, str]]
    display_name: str | None
    bio: str | None
    date_birthday: date | None
    skills: set[str]
    contacts: list[ContactDTO]


class AvatarPresignResponse(BaseModel):
    url: str
    fields: dict[str, str]
    key_base: str

