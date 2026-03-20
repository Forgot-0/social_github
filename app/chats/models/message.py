from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger, Boolean, Enum as SAEnum,
    ForeignKey, Index, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin

if TYPE_CHECKING:
    from app.chats.models.chat import Chat


class MessageStatus(PyEnum):
    sent = "sent"
    delivered = "delivered"
    read = "read"

class MessageType(str, PyEnum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    REPLY = "reply"

class Message(BaseModel, DateMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    type: Mapped[MessageType] = mapped_column(SAEnum(MessageType), default=MessageType.TEXT, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)

    reply_to_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("messages.id"), nullable=True)

    media_url:Mapped[str | None] = mapped_column(String(1024))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    chat: Mapped["Chat"] = relationship(back_populates="messages", lazy="noload")
    reply_to: Mapped[Optional["Message"]] = relationship(remote_side="Message.id", lazy="noload")

    __table_args__ = (
        Index("ix_messages_chat_id_created", "chat_id", "created_at"),
        Index("ix_messages_chat_id_id", "chat_id", "id"),
        Index("ix_messages_chat_not_deleted", "chat_id", "id", postgresql_where="is_deleted = false"),
    )
