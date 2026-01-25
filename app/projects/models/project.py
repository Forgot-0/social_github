from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Enum as SAEnum, Integer, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.projects.models.member import ProjectMembership


class SetArrayString(TypeDecorator):
    impl = ARRAY(String(50))
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, set):
            return list(v.lower() for v in value)
        return list(v.lower() for v in value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return set(value)


class ProjectVisibility(Enum):
    private = "private"
    internal = "internal"
    public = "public"


class Project(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(210), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

    visibility: Mapped[ProjectVisibility] = mapped_column(
        SAEnum(ProjectVisibility), nullable=False, server_default=ProjectVisibility.public.name
    )
    meta_data: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    tags: Mapped[set[str]] = mapped_column(SetArrayString())

    memberships: Mapped[list[ProjectMembership]] = relationship("ProjectMembership", back_populates="project")

