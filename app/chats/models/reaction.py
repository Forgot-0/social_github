from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID, uuid7

from sqlalchemy import (
    UUID as SAUUID,
    BigInteger,
    DateTime,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin
from app.core.events.event import BaseEvent
from app.core.utils import now_utc


@dataclass(frozen=True)
class ReactionUpdatedEvent(BaseEvent):
    message_id: str
    chat_id: str
    emoji: str
    count: int
    changed_by: int

    __event_name__ = "chats.message.reaction_updated"

    def get_aggregate_id(self) -> str:
        return str(self.chat_id)


class MessageReaction(BaseModel, DateMixin):
    __tablename__ = "message_reactions"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True, default=uuid7)

    chat_id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), nullable=False)
    message_id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    emoji: Mapped[str] = mapped_column(String(32), nullable=False)

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_message_reactions_message_user"),
        Index("ix_message_reactions_message_id", "message_id"),
        Index("ix_message_reactions_message_emoji", "message_id", "emoji"),
        Index("ix_message_reactions_chat_message", "chat_id", "message_id"),
        Index("ix_message_reactions_user_message", "user_id", "message_id"),
    )

    @classmethod
    def create(cls, chat_id: UUID, message_id: UUID, user_id: int, emoji: str) -> Self:
        return cls(
            id=uuid7(),
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
        )


class MessageReactionCounter(BaseModel):
    __tablename__ = "message_reaction_counters"

    message_id: Mapped[UUID] = mapped_column(
        SAUUID(as_uuid=True), primary_key=True, autoincrement=False
    )
    emoji: Mapped[str] = mapped_column(String(32), primary_key=True)
    count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc
    )

    __table_args__ = (
        Index("ix_message_reaction_counters_message_id", "message_id"),
    )
