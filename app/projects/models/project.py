from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Self

from sqlalchemy import  Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.core.utils import now_utc
from app.projects.config import project_config
from app.projects.exceptions import TooLongTagNameException
from app.projects.models.base import SetArrayString
from app.projects.models.role_permissions import ProjectRolesEnum

if TYPE_CHECKING:
    from app.projects.models.member import ProjectMembership, MembershipStatus


class ProjectVisibility(Enum):
    private = "private"
    internal = "internal"
    public = "public"

# [
#     "member:read", "member:invite", "member:kick", "member:update",
#     "project:read", "project:write", "project:visibility", "project:delete"
#     "permission:update", "permission:delete"
#     ""
# ]

class Project(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True)

    name: Mapped[str] = mapped_column(String(project_config.MAX_LEN_NAME), nullable=False)
    slug: Mapped[str] = mapped_column(String(project_config.MAX_LEN_SLUG), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

    visibility: Mapped[ProjectVisibility] = mapped_column(
        SAEnum(ProjectVisibility), nullable=False, server_default=ProjectVisibility.public.name
    )
    meta_data: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    tags: Mapped[set[str]] = mapped_column(SetArrayString())

    memberships: Mapped[list["ProjectMembership"]] = relationship(
        "ProjectMembership",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    @classmethod
    def create(
        cls,  owner_id: int, name: str, slug: str,
        description: str, visibility=ProjectVisibility.public,
        metadata: dict[str, Any] | None=None,
        tags: set[str] | None=None
    ) -> Self:
        instance = cls(
            owner_id=owner_id,
            name=name,
            slug=slug,
            description=description,
            visibility=visibility,
            meta_data=metadata or {},
            tags=tags or set()
        )
        instance.memberships.append(
            ProjectMembership(
                user_id=owner_id,
                invited_by=owner_id,
                role_id=ProjectRolesEnum.OWNER.value.id,
                status=MembershipStatus.active,
                joined_at=now_utc(),
            )
        )

        instance._validate_name(name)
        instance._validate_slug(slug)
        instance._validate_tags(instance.tags)

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

    def update_name(self, name: str) -> None:
        self._validate_name(name)
        self.name = name

    def update_description(self, description: str) -> None:
        self.description = description

    def update_visibility(self, visibility: str) -> None:
        self.visibility = ProjectVisibility(visibility)

    def update_tags(self, tags: set[str]) -> None:
        self._validate_tags(tags)
        self.tags = tags

    def get_memeber_by_user_id(self, user_id: int) -> Optional["ProjectMembership"]:
        for member in self.memberships:
            if member.user_id == user_id:
                return member

    def _validate_tags(self, tags: set[str]) -> None:
        for tag in tags:
            if len(tag) > project_config.MAX_LEN_TAG:
                raise TooLongTagNameException(name=tag)

    def _validate_name(self, name: str) -> None:
        if len(name) > project_config.MAX_LEN_NAME:
            raise 

    def _validate_slug(self, slug: str) -> None:
        if len(slug) > project_config.MAX_LEN_SLUG:
            raise 
