from enum import Enum

from app.projects.models.role import ProjectRole



class ProjectRolesEnum(Enum):
    OWNER = ProjectRole(
        id=1,
        name="owner",
        level=9,
        permissions={
            "member:read": True, "member:invite": True, "member:kick": True, "member:udpate": True,
            "project:read": True, "project:update": True, "project:visibility": True, "project:delete": True,
            "position:create": True, "position:update": True, "position:delete": True,
            "permission:update": True,
        }
    )

    MAINTAINER = ProjectRole(
        id=2,
        name="maintainer",
        level=8,
        permissions={
            "member:read": True, "member:invite": True, "member:kick": True, "member:udpate": True,
            "project:read": True, "project:update": True, "project:visibility": True, "project:delete": False,
            "position:create": True, "position:update": True, "position:delete": True,
            "permission:update": True,
        }
    )

    DEVELOPER = ProjectRole(
        id=4,
        name="developer",
        level=7,
        permissions={
            "member:read": True, "member:invite": False, "member:kick": False, "member:udpate": False,
            "project:read": True, "project:update": True, "project:visibility": False, "project:delete": False,
            "position:create": True, "position:update": True, "position:delete": False,
            "permission:update": False,
        }
    )

    USER = ProjectRole(
        id=5,
        name="user",
        level=1,
        permissions={
            "member:read": True, "member:invite": False, "member:kick": False, "member:udpate": False,
            "project:read": True, "project:update": False, "project:visibility": False, "project:delete": False,
            "position:create": False, "position:update": False, "position:delete": False,
            "permission:update": False,
        }
    )

    @classmethod
    def get_all_project_roles(cls) -> list[ProjectRole]:
        return [role.value for role in cls]

