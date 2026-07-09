from pydantic import BaseModel, ConfigDict


class ProjectRoleDTO(BaseModel):
    id: int
    name: str
    permissions: dict

    model_config = ConfigDict(from_attributes=True)
