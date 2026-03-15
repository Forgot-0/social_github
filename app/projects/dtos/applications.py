from uuid import UUID

from pydantic import BaseModel


class ApplicationDTO(BaseModel):
    id: UUID
    project_id: int
    position_id: UUID
    candidate_id: int
    status: str
    message: str | None
    decided_by: int | None
    decided_at: str | None

