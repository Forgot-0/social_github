from pydantic import BaseModel


class ProjectCreateRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None
    visibility: str | None = None
    meta_data: dict | None = None
    tags: set[str] | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None
    meta_data: dict | None = None
    tags: set[str] | None = None


class InviteMemberRequest(BaseModel):
    user_id: int
    role_id: int
    permissions_overrides: dict | None = None

