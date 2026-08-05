from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    UUID as SAUUID,
    BigInteger,
    DateTime,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin


class ChatUserProfile(BaseModel, DateMixin):
    __tablename__ = "chat_user_profiles"

    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, primary_key=True, autoincrement=False
    )

    username: Mapped[str | None] = mapped_column(String, nullable=True)

    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    avatars: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)

    last_event_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    @classmethod
    def create(
        cls,
        user_id: int,
        username: str | None,
        display_name: str | None = None,
        avatars: dict | None = None,
        last_event_id: UUID | None = None,
        source_updated_at: datetime | None = None,
    ) -> ChatUserProfile:
        instance = cls(
            user_id=user_id,
            username=username,
            display_name=display_name,
            avatars=avatars or {},
            last_event_id=last_event_id,
            source_updated_at=source_updated_at,
        )
        return instance
