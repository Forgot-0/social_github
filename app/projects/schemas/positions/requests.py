from pydantic import BaseModel


class PositionCreateRequest(BaseModel):
    title: str
    description: str
    responsibilities: str | None = None

    required_skills: set[str] | None = None

    location_type: str | None = None
    expected_load: str | None = None


class PositionUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    responsibilities: str | None = None

    required_skills: set[str] | None = None

    location_type: str | None = None
    expected_load: str | None = None

