from dataclasses import dataclass
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.models.chat_members import ChatMember
from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.core.events.event import BaseEvent
from app.core.utils import now_utc

if TYPE_CHECKING:
    from app.chats.models.message import Message



class ChatType(str, PyEnum):
    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"


class Chat(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)
    name: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(String(1024))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    last_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    members:  Mapped[list["ChatMember"]] = relationship(back_populates="chat", lazy="noload")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat",  lazy="noload")

    __table_args__ = (
        Index("ix_chats_type_public", "type", "is_public"),
        Index("ix_chats_last_activity", "last_activity_at"),
    )
