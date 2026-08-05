from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Self
from uuid import UUID, uuid7

from sqlalchemy import (
    UUID as SAUUID,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin
from app.core.utils import now_utc


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class OutboxMessage(BaseModel, DateMixin):
    __tablename__ = "outbox_messages"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True, default=uuid7)

    aggregate_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(128), nullable=False)

    event_name: Mapped[str] = mapped_column(String(128), nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    headers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[OutboxStatus] = mapped_column(
        SAEnum(OutboxStatus, name="outbox_status"),
        nullable=False,
        default=OutboxStatus.PENDING,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "ix_outbox_pending_available",
            "available_at",
            "id",
            postgresql_where="status = 'PENDING'",
        ),
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
        Index("ix_outbox_failed", "id", postgresql_where="status = 'FAILED'"),
        Index("ix_outbox_published_at", "published_at"),
    )

    @classmethod
    def create(
        cls,
        *,
        aggregate_id: str,
        event_name: str,
        payload: dict[str, Any],
        headers: dict[str, Any] | None = None,
    ) -> Self:
        return cls(
            id=uuid7(),
            aggregate_type=event_name.split(".")[1],
            aggregate_id=aggregate_id,
            event_name=event_name,
            topic=event_name.split(".", maxsplit=1)[0],
            payload=payload,
            headers=headers or {},
            status=OutboxStatus.PENDING,
            attempts=0,
            available_at=now_utc(),
        )

    def mark_published(self) -> None:
        self.status = OutboxStatus.PUBLISHED
        self.published_at = now_utc()
        self.last_error = None

    def mark_retry(self, error: str, delay_seconds: float) -> None:
        self.attempts += 1
        self.status = OutboxStatus.PENDING
        self.available_at = now_utc() + timedelta(seconds=delay_seconds)
        self.last_error = error[:2000]

    def mark_failed(self, error: str) -> None:
        self.attempts += 1
        self.status = OutboxStatus.FAILED
        self.last_error = error[:2000]
