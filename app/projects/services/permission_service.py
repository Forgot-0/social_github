from dataclasses import dataclass

from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManagerInterface
from app.projects.models.member import MembershipStatus
from app.projects.models.project import Project, ProjectVisibility
from app.projects.models.role import ProjectRole


@dataclass
class ProjectPermissionService:
    rbac_manager: RBACManagerInterface

    def can_update(
        self,
        user_jwt_data: UserJWTData,
        project: Project,
        must_permissions: set[str]
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"project:update"}
        ):
            return True

        if int(user_jwt_data.id) == project.owner_id:
            return True

        member = project.get_member_by_user_id(int(user_jwt_data.id))
        if member is None or member.status != MembershipStatus.active:
            return False

        member_permissions = member.effective_permissions()
        return all(member_permissions.get(perm, False) for perm in must_permissions)

    def can_invite(
        self,
        user_jwt_data: UserJWTData,
        project: Project,
        role: ProjectRole
    ) -> bool:
        if self.rbac_manager.check_permission(
            user_jwt_data, {"project:update"}
        ):
            return True

        if int(user_jwt_data.id) == project.owner_id:
            return True

        member = project.get_member_by_user_id(int(user_jwt_data.id))
        if member is None or member.status != MembershipStatus.active:
            return False

        member_permissions = member.effective_permissions()
        if not member_permissions.get("member:invite", False):
            return False

        return member.role.level > role.level

    def can_view(
        self,
        user_jwt_data: UserJWTData,
        project: Project,
    ) -> bool:
        if project.visibility == ProjectVisibility.public:
            return True

        if self.rbac_manager.check_permission(
            user_jwt_data, {"project:update"}
        ):
            return True

        if int(user_jwt_data.id) == project.owner_id:
            return True

        member = project.get_member_by_user_id(int(user_jwt_data.id))
        return member is not None and member.status == MembershipStatus.active
