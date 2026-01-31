from datetime import datetime
from pydantic import BaseModel


class MemberDTO(BaseModel):
    id: int
    project_id: int
    user_id: int
    role_id: int | None
    status: str
    invited_by: int | None
    joined_at: datetime | None
    permissions: dict = {}

