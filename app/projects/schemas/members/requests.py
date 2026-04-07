from pydantic import BaseModel


class MemberUpdatePermissionsRequest(BaseModel):
    permissions_overrides: dict

class MemberChangeRoleRequest(BaseModel):
    role_id: int
