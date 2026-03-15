import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.auth.dto import UserJWTData
from app.projects.models.member import MembershipStatus, ProjectMembership
from app.projects.models.project import Project, ProjectVisibility
from app.projects.models.position import Position, PositionLocationType, PositionLoad
from app.projects.models.application import Application
from app.projects.models.role_permissions import ProjectRolesEnum

from app.core.utils import now_utc



@pytest_asyncio.fixture
async def persisted_project(
    db_session: AsyncSession,
    user_jwt: UserJWTData,
) -> Project:
    project = Project.create(
        owner_id=int(user_jwt.id),
        name="Integration Test Project",
        slug="integration-test-project",
        small_description="short desc",
        full_description="full desc",
        visibility=ProjectVisibility.public,
        metadata={},
        tags={"python", "fastapi"},
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def persisted_project_with_members(
    db_session: AsyncSession,
    user_jwt: UserJWTData,
) -> Project:

    project = Project.create(
        owner_id=int(user_jwt.id),
        name="Project With Members",
        slug="project-with-members",
        small_description="",
        full_description="",
        visibility=ProjectVisibility.public,
        metadata={},
        tags=set(),
    )
    db_session.add(project)
    await db_session.flush()

    extra_member = ProjectMembership(
        project_id=project.id,
        user_id=999,
        role_id=ProjectRolesEnum.USER.value.id,
        invited_by=int(user_jwt.id),
        status=MembershipStatus.active,
        joined_at=now_utc(),
        permissions_overrides={},
    )
    db_session.add(extra_member)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def persisted_position(
    db_session: AsyncSession,
    persisted_project: Project,
) -> Position:
    position = Position.create(
        project_id=persisted_project.id,
        title="Backend Developer",
        description="We need a backend dev",
        required_skills={"python", "fastapi"},
        responsibilities="Write code",
        location_type=PositionLocationType.remote,
        expected_load=PositionLoad.low,
    )
    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)
    return position


@pytest_asyncio.fixture
async def persisted_application(
    db_session: AsyncSession,
    persisted_position: Position,
) -> Application:
    application = Application.create(
        project_id=persisted_position.project_id,
        position_id=persisted_position.id,
        candidate_id=777,
        message="I want to join",
    )
    db_session.add(application)
    await db_session.commit()
    await db_session.refresh(application)
    return application
