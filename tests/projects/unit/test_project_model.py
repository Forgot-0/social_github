import pytest

from app.projects.config import project_config
from app.projects.exceptions import (
    MaxPositionsPerProjectLimitExceededException,
    TooLongTagNameException,
)
from app.projects.models.member import MembershipStatus
from app.projects.models.project import CreatedPositionEvent, Project, ProjectVisibility


def make_project(owner_id: int = 1, name: str = "Test Project", slug: str = "test-project") -> Project:
    return Project.create(
        owner_id=owner_id,
        name=name,
        slug=slug,
        small_description="short",
        full_description="long",
        visibility=ProjectVisibility.public,
        metadata={},
        tags=set(),
    )


@pytest.mark.unit
@pytest.mark.projects
class TestProjectCreate:

    def test_create_adds_owner_as_active_member(self) -> None:
        project = make_project(owner_id=42)

        assert len(project.memberships) == 1
        member = project.memberships[0]
        assert member.user_id == 42
        assert member.status == MembershipStatus.active

    def test_create_with_tags(self) -> None:
        project = Project.create(
            owner_id=1,
            name="Tagged",
            slug="tagged",
            small_description="",
            full_description="",
            visibility=ProjectVisibility.public,
            metadata={},
            tags={"python", "fastapi"},
        )

        assert set(project.tags) == {"python", "fastapi"}

    def test_create_with_too_long_tag_raises(self) -> None:
        with pytest.raises(TooLongTagNameException):
            Project.create(
                owner_id=1,
                name="Bad tags",
                slug="bad-tags",
                small_description="",
                full_description="",
                visibility=ProjectVisibility.public,
                metadata={},
                tags={"x" * (project_config.MAX_LEN_TAG + 1)},
            )


@pytest.mark.unit
@pytest.mark.projects
class TestProjectInviteMember:

    def test_invite_member_adds_to_memberships(self) -> None:
        project = make_project(owner_id=1)

        project.invite_memeber(user_id=2, role_id=5, invited_by=1)

        assert len(project.memberships) == 2
        invited = project.get_memeber_by_user_id(2)
        assert invited is not None
        assert invited.status == MembershipStatus.invited

    def test_invite_self_raises(self) -> None:
        project = make_project(owner_id=1)

        with pytest.raises(Exception):
            project.invite_memeber(user_id=1, role_id=5, invited_by=1)

    def test_invite_already_member_raises(self) -> None:
        project = make_project(owner_id=1)
        project.invite_memeber(user_id=2, role_id=5, invited_by=1)

        with pytest.raises(Exception):
            project.invite_memeber(user_id=2, role_id=5, invited_by=1)

    def test_invite_with_permissions_overrides(self) -> None:
        project = make_project(owner_id=1)
        overrides = {"project:update": False}

        project.invite_memeber(user_id=2, role_id=5, invited_by=1, permissions_overrides=overrides)

        member = project.get_memeber_by_user_id(2)
        assert member is not None
        assert member.permissions_overrides == overrides

    def test_get_member_by_user_id_not_found_returns_none(self) -> None:
        project = make_project(owner_id=1)

        assert project.get_memeber_by_user_id(999) is None


@pytest.mark.unit
@pytest.mark.projects
class TestProjectNewPosition:

    def test_new_position_registers_event(self) -> None:
        project = make_project()

        project.new_position(
            title="Backend Dev",
            description="desc",
            required_skills={"python"},
            responsibilities=None,
            location_type=None,
            expected_load=None,
        )

        events = project.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], CreatedPositionEvent)
        assert events[0].project_id == project.id

    def test_pull_events_clears_after_call(self) -> None:
        project = make_project()
        project.new_position(
            title="Dev",
            description="desc",
            required_skills={"go"},
            responsibilities=None,
            location_type=None,
            expected_load=None,
        )

        project.pull_events()

        assert project.pull_events() == []

    def test_new_position_respects_limit(self) -> None:
        project = make_project()

        for i in range(project_config.MAX_POSITIONS_PER_PROJECT):
            project.new_position(
                title=f"Position {i}",
                description="desc",
                required_skills={"skill"},
                responsibilities=None,
                location_type=None,
                expected_load=None,
            )

        with pytest.raises(MaxPositionsPerProjectLimitExceededException):
            project.new_position(
                title="Overflow",
                description="desc",
                required_skills={"skill"},
                responsibilities=None,
                location_type=None,
                expected_load=None,
            )


@pytest.mark.unit
@pytest.mark.projects
class TestProjectUpdate:

    def test_update_name(self) -> None:
        project = make_project()
        project.update_name("New Name")
        assert project.name == "New Name"

    def test_update_description(self) -> None:
        project = make_project()
        project.update_description("New description")
        assert project.small_description == "New description"

    def test_update_visibility(self) -> None:
        project = make_project()
        project.update_visibility("private")
        assert project.visibility == ProjectVisibility.private

    def test_update_tags(self) -> None:
        project = make_project()
        project.update_tags({"rust", "wasm"})
        assert set(project.tags) == {"rust", "wasm"}

    def test_update_tags_with_too_long_name_raises(self) -> None:
        project = make_project()
        with pytest.raises(TooLongTagNameException):
            project.update_tags({"x" * (project_config.MAX_LEN_TAG + 1)})