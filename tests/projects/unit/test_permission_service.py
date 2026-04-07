from typing import Callable

import pytest

from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.projects.models.member import MembershipStatus, ProjectMembership
from app.projects.models.project import Project, ProjectVisibility
from app.projects.models.role import ProjectRole
from app.projects.services.permission_service import ProjectPermissionService


def make_role(level: int = 1, permissions: dict | None = None) -> ProjectRole:
    return ProjectRole(
        id=5,
        name="user",
        level=level,
        permissions=permissions or {},
    )


def make_project(owner_id: int = 1, visibility: ProjectVisibility = ProjectVisibility.public) -> Project:
    p = Project(
        id=100,
        owner_id=owner_id,
        name="Test",
        slug="test",
        small_description="",
        full_description="",
        visibility=visibility,
        meta_data={},
        tags=[],
    )
    p.memberships = []
    return p


def add_member(
    project: Project,
    user_id: int,
    status: MembershipStatus = MembershipStatus.active,
    role_permissions: dict | None = None,
    overrides: dict | None = None,
    role_level: int = 1,
) -> ProjectMembership:
    role = make_role(level=role_level, permissions=role_permissions or {})
    m = ProjectMembership(
        id=user_id,
        project_id=project.id,
        user_id=user_id,
        role_id=5,
        invited_by=1,
        status=status,
        permissions_overrides=overrides or {},
    )
    m.role = role
    project.memberships.append(m)
    return m


def make_jwt(user_id: str = "2", roles: list[str] | None = None, permissions: list[str] | None = None) -> UserJWTData:
    return UserJWTData(
        id=user_id,
        username="user",
        roles=roles or ["user"],
        permissions=permissions or [],
        security_level=1,
        device_id="dev",
    )


@pytest.fixture
def service() -> ProjectPermissionService:
    return ProjectPermissionService(rbac_manager=RBACManager())


@pytest.mark.unit
@pytest.mark.projects
class TestCanUpdate:

    def test_owner_can_update(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        jwt = make_jwt(user_id="1")

        assert service.can_update(jwt, project, {"project:update"}) is True

    def test_super_admin_can_update(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        jwt = make_jwt(user_id="99", roles=["super_admin"])

        assert service.can_update(jwt, project, {"project:update"}) is True

    def test_active_member_with_permission_can_update(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        add_member(project, user_id=2, role_permissions={"project:update": True})
        jwt = make_jwt(user_id="2")

        assert service.can_update(jwt, project, {"project:update"}) is True

    def test_active_member_without_permission_cannot_update(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        add_member(project, user_id=2, role_permissions={"project:update": False})
        jwt = make_jwt(user_id="2")

        assert service.can_update(jwt, project, {"project:update"}) is False

    def test_non_member_cannot_update(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        jwt = make_jwt(user_id="99")

        assert service.can_update(jwt, project, {"project:update"}) is False

    def test_suspended_member_cannot_update(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        add_member(project, user_id=2, status=MembershipStatus.suspended, role_permissions={"project:update": True})
        jwt = make_jwt(user_id="2")

        assert service.can_update(jwt, project, {"project:update"}) is False

    def test_invited_member_cannot_update(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        add_member(project, user_id=2, status=MembershipStatus.invited, role_permissions={"project:update": True})
        jwt = make_jwt(user_id="2")

        assert service.can_update(jwt, project, {"project:update"}) is False

    def test_permission_override_grants_access(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        add_member(project, user_id=2, role_permissions={"position:create": False}, overrides={"position:create": True})
        jwt = make_jwt(user_id="2")

        assert service.can_update(jwt, project, {"position:create"}) is True

    def test_all_required_permissions_must_be_present(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        add_member(
            project,
            user_id=2,
            role_permissions={"member:update": True, "permission:update": False},
        )
        jwt = make_jwt(user_id="2")

        assert service.can_update(jwt, project, {"member:update", "permission:update"}) is False


@pytest.mark.unit
@pytest.mark.projects
class TestCanInvite:

    def test_owner_can_invite_any_role(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        role = make_role(level=8)
        jwt = make_jwt(user_id="1")

        assert service.can_invite(jwt, project, role) is True

    def test_super_admin_can_invite(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        role = make_role(level=9)
        jwt = make_jwt(user_id="99", roles=["super_admin"])

        assert service.can_invite(jwt, project, role) is True

    def test_member_cannot_invite_higher_level_role(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        add_member(project, user_id=2, role_level=3, role_permissions={"member:invite": True})
        invitee_role = make_role(level=5)
        jwt = make_jwt(user_id="2")

        assert service.can_invite(jwt, project, invitee_role) is False

    def test_non_member_cannot_invite(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1)
        role = make_role(level=1)
        jwt = make_jwt(user_id="50")

        assert service.can_invite(jwt, project, role) is False


@pytest.mark.unit
@pytest.mark.projects
class TestCanView:

    def test_public_project_visible_to_anyone(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1, visibility=ProjectVisibility.public)
        jwt = make_jwt(user_id="99")

        assert service.can_view(jwt, project) is True

    def test_private_project_owner_can_view(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1, visibility=ProjectVisibility.private)
        jwt = make_jwt(user_id="1")

        assert service.can_view(jwt, project) is True

    def test_private_project_super_admin_can_view(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1, visibility=ProjectVisibility.private)
        jwt = make_jwt(user_id="99", roles=["super_admin"])

        assert service.can_view(jwt, project) is True

    def test_private_project_stranger_cannot_view(self, service: ProjectPermissionService) -> None:
        project = make_project(owner_id=1, visibility=ProjectVisibility.private)
        jwt = make_jwt(user_id="99")

        assert service.can_view(jwt, project) is False
