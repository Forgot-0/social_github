from datetime import date

from pydantic import BaseModel, ConfigDict

from app.profiles.dtos.contacts import ContactDTO


class ProfileDTO(BaseModel):
    id: int
    avatars: dict[int, dict[str, str]]
    specialization: str | None
    display_name: str | None
    bio: str | None
    date_birthday: date | None
    skills: set[str]
    contacts: list[ContactDTO]

    model_config = ConfigDict(from_attributes=True)


class AvatarPresignResponse(BaseModel):
    url: str
    fields: dict[str, str]
    key_base: str

