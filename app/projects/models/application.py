from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import UUID, BigInteger, DateTime, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin
from app.core.utils import now_utc


class ApplicationStatus(PyEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Application(BaseModel, DateMixin):
    __tablename__ = "applications"

    id: Mapped[PyUUID] = mapped_column(UUID, primary_key=True)

    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    position_id: Mapped[PyUUID] = mapped_column(UUID, nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus), nullable=False, server_default=ApplicationStatus.pending.name
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    decided_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @classmethod
    def create(
        cls,
        project_id: int,
        position_id: PyUUID,
        candidate_id: int,
        message: str | None = None,
    ) -> "Application":
        return cls(
            id=uuid4(),
            project_id=project_id,
            position_id=position_id,
            candidate_id=candidate_id,
            status=ApplicationStatus.pending,
            message=message,
        )

    def accept(self, decided_by: int) -> None:
        if self.status != ApplicationStatus.pending:
            raise

        self.status = ApplicationStatus.accepted
        self.decided_by = decided_by
        self.decided_at = now_utc()

    def reject(self, decided_by: int) -> None:
        if self.status != ApplicationStatus.pending:
            raise

        self.status = ApplicationStatus.rejected
        self.decided_by = decided_by
        self.decided_at = now_utc()

