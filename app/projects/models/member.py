from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel, DateMixin

if TYPE_CHECKING:
    from app.projects.models.project import Project
    from app.projects.models.role import ProjectRole


class MembershipStatus(PyEnum):
    invited = "invited"
    pending = "pending"
    active = "active"
    suspended = "suspended"
    removed = "removed"


class ProjectMembership(BaseModel, DateMixin):
    __tablename__ = "project_memberships"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[MembershipStatus] = mapped_column(
        SAEnum(MembershipStatus), nullable=False, server_default=MembershipStatus.invited.name
    )
    invited_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    permissions_overrides: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    project: Mapped["Project"] = relationship("Project", back_populates="memberships")
    role: Mapped["ProjectRole"] = relationship("ProjectRole")

    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)

    def effective_permissions(self):
        perms = {}
        if self.role and self.role.permissions:
            perms.update(self.role.permissions)
        if self.permissions_overrides:
            perms.update(self.permissions_overrides)
        return perms
