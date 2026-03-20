from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum as SAEnum,
    ForeignKey, Index, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel

if TYPE_CHECKING:
    from app.chats.models.chat import Chat


class MessageStatus(PyEnum):
    sent = "sent"
    delivered = "delivered"
    read = "read"


class Message(BaseModel):
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_chat_cursor", "chat_id", "id"),
        Index("idx_messages_chat_time", "chat_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
