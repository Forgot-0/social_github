from dataclasses import dataclass
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional, Self

from sqlalchemy import (
    BigInteger, Boolean, Enum as SAEnum,
    ForeignKey, Index, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.config import chat_config
from app.chats.exceptions import MessageTooLongException
from app.core.db.base_model import BaseModel, DateMixin
from app.core.events.event import BaseEvent

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


@dataclass(frozen=True)
class ModifyMessageEvent(BaseEvent):
    message_id: int
    new_content: str
    chat_id: int

    __event_name__ = ""

@dataclass(frozen=True)
class DeletedMessageEvent(BaseEvent):
    message_id: int
    chat_id: int
    deleted_by: int

    __event_name__ = ""


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

    @classmethod
    def create(
        cls,
        sender_id: int,
        chat_id: int,
        content: str,
        reply_to_id: int | None = None,
        message_type: MessageType = MessageType.TEXT,
    ) -> Self:
        instance = cls(
            sender_id=sender_id,
            chat_id=chat_id,
            content=content,
            reply_to_id=reply_to_id,
            type=message_type
        )
        instance.validate_content()
        return instance

    def update_content(self, new_content: str) -> None:
        self.content = new_content
        self.validate_content()
        self.register_event(
            ModifyMessageEvent(
                self.id, new_content, self.chat_id
            )
        )

    def delete(self, deleted_by: int) -> None:
        self.is_deleted = True
        self.register_event(
            DeletedMessageEvent(
                message_id=self.id, chat_id=self.chat_id, deleted_by=deleted_by
            )
        )

    def validate_content(self) -> None:
        if self.content and len(self.content) > chat_config.MAX_MESSAGE_LENGTH:
            raise MessageTooLongException(
                length=len(self.content),
                max_length=chat_config.MAX_MESSAGE_LENGTH,
            )