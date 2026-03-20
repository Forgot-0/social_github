from dataclasses import dataclass
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin

if TYPE_CHECKING:
    from app.chats.models.chat import Chat


class MemberRole(str, PyEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ChatMember(BaseModel, DateMixin):
    __tablename__ = "chat_members"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), nullable=False, default=MemberRole.MEMBER)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    is_muted:  Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    last_read_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    chat: Mapped["Chat"] = relationship(back_populates="members", lazy="noload")

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_chat_member"),
        Index("ix_chat_members_user_chat", "user_id", "chat_id"),
        Index("ix_chat_members_chat_user", "chat_id", "user_id"),
    )

