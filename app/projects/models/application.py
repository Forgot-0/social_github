from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UUID as SAUUID, BigInteger, DateTime, Enum as SAEnum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin
from app.core.utils import now_utc
from app.projects.exceptions import NotPendingStatusApplicationError

if TYPE_CHECKING:
    from app.projects.models.position import Position
    from app.projects.models.project import Project


class ApplicationStatus(StrEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Application(BaseModel, DateMixin):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("project_id", "position_id", "candidate_id", name="unique_id"),
    )

    id: Mapped[UUID] = mapped_column(SAUUID, primary_key=True)

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"),
        nullable=False, index=True
    )

    position_id: Mapped[UUID] = mapped_column(
        SAUUID, ForeignKey("positions.id"),
        nullable=False, index=True
    )

    candidate_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus), nullable=False, server_default=ApplicationStatus.pending.name
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    decided_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project", lazy="selectin", back_populates="applications")
    position: Mapped["Position"] = relationship("Position", lazy="selectin", back_populates="applications")

    @classmethod
    def create(
        cls,
        project_id: int,
        position_id: UUID,
        candidate_id: int,
        message: str | None = None,
    ) -> "Application":
        instance = cls(
            id=uuid4(),
            project_id=project_id,
            position_id=position_id,
            candidate_id=candidate_id,
            status=ApplicationStatus.pending,
            message=message,
        )

        return instance

    def accept(self, decided_by: int) -> None:
        if self.status != ApplicationStatus.pending:
            raise NotPendingStatusApplicationError

        self.status = ApplicationStatus.accepted
        self.decided_by = decided_by
        self.decided_at = now_utc()
        self.position.close()

    def reject(self, decided_by: int) -> None:
        if self.status != ApplicationStatus.pending:
            raise NotPendingStatusApplicationError

        self.status = ApplicationStatus.rejected
        self.decided_by = decided_by
        self.decided_at = now_utc()

