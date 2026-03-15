from uuid import UUID

from pydantic import BaseModel


class ApplicationCreateRequest(BaseModel):
    message: str | None = None


class ApplicationDecisionRequest(BaseModel):
    application_id: UUID

