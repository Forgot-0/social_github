from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.projects.dtos.members import MemberDTO


class ProjectDTO(BaseModel):
    id: int
    owner_id: int
    name: str
    slug: str
    small_description: str | None
    full_description: str | None
    visibility: str
    meta_data: dict[str, Any]
    tags: list[str]
    created_at: datetime | None
    updated_at: datetime | None
    memberships: list[MemberDTO] = Field(default_factory=list)

