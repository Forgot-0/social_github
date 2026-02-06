from dataclasses import dataclass

from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.projects.models.member import MembershipStatus
from app.projects.models.project import Project, ProjectVisibility
from app.projects.models.role import ProjectRole


@dataclass
class ProjectPermissionService:
    rbac_manager: RBACManager

    def can_update(
        self,
        user_jwt_data: UserJWTData,
        project: Project,
        must_permissions: set[str]
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"project:update"}
        ): return True

        if int(user_jwt_data.id) == project.owner_id:
            return True

        memeber = project.get_memeber_by_user_id(int(user_jwt_data.id))
        if memeber is None or memeber.status != MembershipStatus.active:
            return False

        memeber_permissions = memeber.effective_permissions()
        for perm in must_permissions:
            if not memeber_permissions.get(perm, False):
                return False

        return True

    def can_invite(
        self,
        user_jwt_data: UserJWTData,
        project: Project,
        role: ProjectRole
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"project:update"}
        ): return True

        if int(user_jwt_data.id) == project.owner_id:
            return True

        memeber = project.get_memeber_by_user_id(int(user_jwt_data.id))
        if memeber is None or memeber.status != MembershipStatus.active:
            return False

        memeber_permissions = memeber.effective_permissions()
        if not memeber_permissions.get("memebr:invite", False):
            return False

        if memeber.role.level < role.level:
            return False

        return True

    def can_view(
        self,
        user_jwt_data: UserJWTData,
        project: Project,
    ) -> bool:
        if project.visibility == ProjectVisibility.public:
            return True

        if self.rbac_manager.check_permission(
            user_jwt_data, {"project:update"}
        ): return True

        if int(user_jwt_data.id) == project.owner_id:
            return True

        memeber = project.get_memeber_by_user_id(int(user_jwt_data.id))
        if memeber is not None and memeber.status != MembershipStatus.active:
            return True

        return False
