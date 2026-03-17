import pytest
from uuid import uuid4

from app.projects.models.application import Application, ApplicationStatus
from app.projects.models.member import MembershipStatus, ProjectMembership
from app.projects.models.position import Position
from app.projects.models.role import ProjectRole


@pytest.mark.unit
@pytest.mark.projects
class TestApplicationModel:

    def _make_application(self) -> Application:
        application = Application.create(
            project_id=1,
            position_id=uuid4(),
            candidate_id=10,
            message="Please consider me",
        )
        application.position = Position.create(
            1, "test", "test", {"test", }
        )
        return application

    def test_create_has_pending_status(self) -> None:
        app = self._make_application()
        assert app.status == ApplicationStatus.pending
        assert app.decided_by is None
        assert app.decided_at is None

    def test_accept_changes_status(self) -> None:
        app = self._make_application()
        app.accept(decided_by=5)

        assert app.status == ApplicationStatus.accepted
        assert app.decided_by == 5
        assert app.decided_at is not None

    def test_reject_changes_status(self) -> None:
        app = self._make_application()
        app.reject(decided_by=5)

        assert app.status == ApplicationStatus.rejected
        assert app.decided_by == 5
        assert app.decided_at is not None

    def test_accept_already_accepted_raises(self) -> None:
        app = self._make_application()
        app.accept(decided_by=5)

        with pytest.raises(Exception):
            app.accept(decided_by=5)

    def test_reject_already_rejected_raises(self) -> None:
        app = self._make_application()
        app.reject(decided_by=5)

        with pytest.raises(Exception):
            app.reject(decided_by=5)

    def test_accept_already_rejected_raises(self) -> None:
        app = self._make_application()
        app.reject(decided_by=5)

        with pytest.raises(Exception):
            app.accept(decided_by=5)

    def test_reject_already_accepted_raises(self) -> None:
        app = self._make_application()
        app.accept(decided_by=5)

        with pytest.raises(Exception):
            app.reject(decided_by=5)


@pytest.mark.unit
@pytest.mark.projects
class TestProjectMembershipModel:

    def _make_role(self, permissions: dict | None = None) -> ProjectRole:
        return ProjectRole(
            id=5,
            name="user",
            level=1,
            permissions=permissions or {"project:read": True, "project:update": False},
        )

    def _make_membership(
        self,
        status: MembershipStatus = MembershipStatus.invited,
        permissions_overrides: dict | None = None,
    ) -> ProjectMembership:
        role = self._make_role()
        m = ProjectMembership(
            id=1,
            project_id=1,
            user_id=2,
            role_id=5,
            invited_by=1,
            status=status,
            permissions_overrides=permissions_overrides or {},
        )
        m.role = role
        return m

    def test_accept_invite_changes_to_active(self) -> None:
        m = self._make_membership(MembershipStatus.invited)
        m.accept_invite()

        assert m.status == MembershipStatus.active
        assert m.joined_at is not None

    def test_accept_pending_invite_changes_to_active(self) -> None:
        m = self._make_membership(MembershipStatus.pending)
        m.accept_invite()

        assert m.status == MembershipStatus.active

    def test_accept_active_raises(self) -> None:
        m = self._make_membership(MembershipStatus.active)

        with pytest.raises(Exception):
            m.accept_invite()

    def test_reject_invite_changes_to_suspended(self) -> None:
        m = self._make_membership(MembershipStatus.invited)
        m.reject_invite()

        assert m.status == MembershipStatus.suspended

    def test_reject_active_raises(self) -> None:
        m = self._make_membership(MembershipStatus.active)

        with pytest.raises(Exception):
            m.reject_invite()

    def test_effective_permissions_without_overrides(self) -> None:
        m = self._make_membership()
        perms = m.effective_permissions()

        assert perms["project:read"] is True
        assert perms["project:update"] is False

    def test_effective_permissions_override_wins(self) -> None:
        m = self._make_membership(permissions_overrides={"project:update": True})
        perms = m.effective_permissions()

        assert perms["project:update"] is True

    def test_effective_permissions_override_can_remove(self) -> None:
        m = self._make_membership(permissions_overrides={"project:read": False})
        perms = m.effective_permissions()

        assert perms["project:read"] is False
