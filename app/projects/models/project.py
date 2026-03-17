from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Self
from uuid import UUID

from sqlalchemy import  BigInteger, Boolean, Enum as SAEnum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.core.events.event import BaseEvent
from app.core.utils import now_utc
from app.projects.config import project_config
from app.projects.exceptions import (
    MaxPositionsPerProjectLimitExceededException,
    TooLongNameException,
    TooLongTagNameException,
)
from app.projects.models.application import Application
from app.projects.models.position import Position, PositionLoad, PositionLocationType
from app.projects.models.member import MembershipStatus, ProjectMembership


@dataclass(frozen=True)
class CreatedPositionEvent(BaseEvent):
    position_id: str
    project_id: int
    required_skills: list[str]

    __event_name__: str = "positions.created"


class ProjectVisibility(Enum):
    private = "private"
    internal = "internal"
    public = "public"


class ProjectStatus(Enum):
    active = "active"
    archived = "archived"

# [
#     "member:read", "member:invite", "member:kick", "member:update",
#     "project:read", "project:write", "project:visibility", "project:delete"
#     "permission:update", "permission:delete"
#     ""
# ]

class Project(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "projects"
    __table_args__ = (
        Index("idx_projects_tags", "tags", postgresql_using="gin"),
    )


    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)

    name: Mapped[str] = mapped_column(String(project_config.MAX_LEN_NAME), nullable=False)
    slug: Mapped[str] = mapped_column(String(project_config.MAX_LEN_SLUG), nullable=False, index=True)

    small_description: Mapped[str] = mapped_column(String(length=256), nullable=True)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)

    visibility: Mapped[ProjectVisibility] = mapped_column(
        SAEnum(ProjectVisibility), nullable=False, server_default=ProjectVisibility.public.name
    )

    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus), nullable=False, server_default=ProjectStatus.active.name
    )
    meta_data: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    tags: Mapped[list[str]] = mapped_column(ARRAY(String(project_config.MAX_LEN_TAG)))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    memberships: Mapped[list["ProjectMembership"]] = relationship(
        "ProjectMembership",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    positions: Mapped[list["Position"]] = relationship(
        "Position",
        back_populates="project",
        cascade="all, delete"
    )

    applications: Mapped[list[Application]] = relationship(
        "Application",
        back_populates="project",
        cascade="all, delete"
    )

    @classmethod
    def create(
        cls,  owner_id: int, name: str, slug: str,
        small_description: str, full_description: str, visibility=ProjectVisibility.public,
        metadata: dict[str, Any] | None=None,
        tags: set[str] | None=None
    ) -> Self:
        instance = cls(
            owner_id=owner_id,
            name=name,
            slug=slug,
            small_description=small_description,
            full_description=full_description,
            visibility=visibility,
            meta_data=metadata or {},
            tags=tags or set()
        )
        instance.memberships.append(
            ProjectMembership(
                user_id=owner_id,
                invited_by=owner_id,
                role_id=1,#ProjectRolesEnum.OWNER.value.id, Из за этого ошибка импорта 
                status=MembershipStatus.active,
                joined_at=now_utc(),
            )
        )

        instance._validate_name(name)
        instance._validate_slug(slug)

        return instance

    def invite_memeber(
            self, user_id: int, role_id: int, invited_by: int,
            permissions_overrides: dict | None=None
        ) -> None:
        if user_id == invited_by:
            raise

        already_member = self.get_memeber_by_user_id(user_id=user_id)
        if already_member is not None:
            raise

        self.memberships.append(
            ProjectMembership(
                project_id=self.id,
                user_id=user_id,
                role_id=role_id,
                invited_by=invited_by,
                joined_at=None,
                status=MembershipStatus.invited,
                permissions_overrides=permissions_overrides or {}
            )
        )

    def new_position(
        self,
        title: str,
        description: str,
        required_skills: set[str],
        responsibilities: str | None,
        location_type: str | None,
        expected_load: str | None,
    ) -> None:
        if len(self.positions) >= project_config.MAX_POSITIONS_PER_PROJECT:
            raise MaxPositionsPerProjectLimitExceededException(
                project_id=self.id,
                limit=project_config.MAX_POSITIONS_PER_PROJECT,
            )

        position = Position.create(
            project_id=self.id,
            title=title,
            description=description,
            required_skills=required_skills,
            responsibilities=responsibilities,
            location_type=PositionLocationType(location_type) if location_type else PositionLocationType.remote,
            expected_load=PositionLoad(expected_load) if location_type else PositionLoad.low
        )
        self.positions.append(position)

        self.register_event(
            CreatedPositionEvent(
                position_id=str(position.id),
                project_id=self.id,
                required_skills=list(required_skills)
            )
        )


    def update_name(self, name: str) -> None:
        self._validate_name(name)
        self.name = name

    def update_description(self, description: str) -> None:
        self.small_description = description

    def update_visibility(self, visibility: str) -> None:
        self.visibility = ProjectVisibility(visibility)

    def update_tags(self, tags: set[str]) -> None:
        self.tags = list(tags)

    def get_memeber_by_user_id(self, user_id: int) -> Optional["ProjectMembership"]:
        for member in self.memberships:
            if member.user_id == user_id:
                return member

    def get_position_by_id(self, position_id: UUID) -> Optional["Position"]:
        for pos in self.positions:
            if pos.id == position_id:
                return pos

    @validates("tags")
    def validate_tags(self, key, value):

        if len(value) != len(set(value)):
            raise ValueError("Duplicate skills are not allowed")

        for tag in value:
            if len(tag) > project_config.MAX_LEN_TAG:
                raise TooLongTagNameException(name=tag)

        return value

    def _validate_name(self, name: str) -> None:
        if len(name) > project_config.MAX_LEN_NAME:
            raise TooLongNameException(name=name)

    def _validate_slug(self, slug: str) -> None:
        if len(slug) > project_config.MAX_LEN_SLUG:
            raise TooLongNameException(name=slug)
