from dataclasses import dataclass, field

from app.projects.models.member import ProjectMembership
from app.projects.models.project import Project


@dataclass
class ProjectRBACManager:
    system_roles: set[str] = field(
        default_factory=lambda: {"owner", }
    )

    def is_owner(self, memeber: ProjectMembership, project: Project) -> bool:
        return memeber.user_id == project.owner_id

    def check_permission(self, memeber: ProjectMembership, permissions: set[str]) -> bool:
        ...

