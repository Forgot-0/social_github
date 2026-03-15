from uuid import UUID

from pydantic import BaseModel


class PositionDTO(BaseModel):
    id: UUID
    project_id: int

    title: str
    description: str
    responsibilities: str | None

    required_skills: set[str]
    is_open: bool

    location_type: str
    expected_load: str

