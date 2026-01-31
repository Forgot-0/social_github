from pydantic import BaseModel


class RoleDTO(BaseModel):
    id: int
    name: str
    permissions: dict
