from pydantic import BaseModel


class MemberUpdatePermissionsRequest(BaseModel):
    permissions_overrides: dict
