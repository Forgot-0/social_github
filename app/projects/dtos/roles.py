from pydantic import BaseModel


class ProjectRoleDTO(BaseModel):
    id: int
    name: str
    permissions: dict
