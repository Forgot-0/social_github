from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from app.projects.dtos.roles import ProjectRoleDTO

if TYPE_CHECKING:
    from app.projects.dtos.projects import ProjectDTO


class MemberDTO(BaseModel):
    id: int
    project_id: int
    user_id: int
    role_id: int | None
    status: str
    invited_by: int | None
    joined_at: datetime | None
    permissions_overrides: dict

    role: ProjectRoleDTO | None = None
    project: ProjectDTO | None = Field(default=None, repr=False)

    model_config = ConfigDict(from_attributes=True)
