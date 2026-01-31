from datetime import datetime
from pydantic import BaseModel

from app.projects.dtos.members import MemberDTO


class ProjectDTO(BaseModel):
    id: int
    owner_id: int
    name: str
    slug: str
    description: str | None
    visibility: str
    meta_data: dict
    tags: set[str]
    created_at: datetime | None
    updated_at: datetime | None
    memberships: list[MemberDTO] = []

