from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin
from app.core.utils import now_utc
from app.projects.exceptions import NotValidMemberStatusException

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
        BigInteger, ForeignKey("project_roles.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[MembershipStatus] = mapped_column(
        SAEnum(MembershipStatus), nullable=False, server_default=MembershipStatus.invited.name
    )
    invited_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    permissions_overrides: Mapped[dict[str, bool]] = mapped_column(JSONB, server_default="{}")

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="memberships",
    )

    role: Mapped["ProjectRole"] = relationship("ProjectRole")

    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)

    def accept_invite(self) -> None:
        if self.status not in (MembershipStatus.invited, MembershipStatus.pending):
            raise NotValidMemberStatusException(
                member_status=self.status.value,
                action="accept"
            )

        self.status = MembershipStatus.active
        self.joined_at = now_utc()

    def reject_invite(self) -> None:
        if self.status not in (MembershipStatus.invited, MembershipStatus.pending):
            raise NotValidMemberStatusException(
                member_status=self.status.value,
                action="reject"
            )

        self.status = MembershipStatus.suspended

    def effective_permissions(self) -> dict[str, bool]:
        perms = self.role.permissions.copy()
        if self.permissions_overrides:
            perms.update(self.permissions_overrides)
        return perms

