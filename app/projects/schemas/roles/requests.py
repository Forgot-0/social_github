from pydantic import BaseModel


class RoleCreateRequest(BaseModel):
    name: str
    permissions: dict


class RoleUpdateRequest(BaseModel):
    permissions: dict
