from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.projects.dtos.roles import ProjectRoleDTO


class ProjectMemberDTO(BaseModel):
    id: int
    project_id: int
    user_id: int
    role_id: int | None
    status: str
    invited_by: int | None
    joined_at: datetime | None
    permissions_overrides: dict

    role: ProjectRoleDTO | None = None

    model_config = ConfigDict(from_attributes=True)


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
    memberships: list[ProjectMemberDTO] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

