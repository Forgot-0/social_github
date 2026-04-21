from dataclasses import dataclass
from enum import Enum as PyEnum
from html import escape
from typing import TYPE_CHECKING, Optional, Self

from sqlalchemy import BigInteger, Boolean, Enum as SAEnum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.config import chat_config
from app.chats.exceptions import MessageTooLongException
from app.core.db.base_model import BaseModel, DateMixin
from app.core.events.event import BaseEvent
from app.chats.models.attachment import MessageAttachment

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
class ModifiedMessageEvent(BaseEvent):
    message_id: int
    new_content: str
    chat_id: int
    modified_by: int

    __event_name__ = "chats.message.modified"

    def get_partition_key(self) -> str:
        return str(self.chat_id)


@dataclass(frozen=True)
class DeletedMessageEvent(BaseEvent):
    message_id: int
    chat_id: int
    deleted_by: int

    __event_name__ = "chats.message.deleted"

    def get_partition_key(self) -> str:
        return str(self.chat_id)


class Message(BaseModel, DateMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    type: Mapped[MessageType] = mapped_column(
        SAEnum(MessageType), default=MessageType.TEXT, nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text)

    reply_to_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("messages.id"), nullable=True
    )

    forwarded_from_chat_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("chats.id", ondelete="SET NULL"), nullable=True
    )
    forwarded_from_message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    chat: Mapped["Chat"] = relationship(back_populates="messages", foreign_keys=[chat_id], lazy="noload")
    reply_to: Mapped[Optional["Message"]] = relationship(
        foreign_keys=[reply_to_id], remote_side="Message.id", lazy="noload"
    )
    forwarded_from: Mapped[Optional["Message"]] = relationship(
        foreign_keys=[forwarded_from_message_id], remote_side="Message.id", lazy="noload"
    )
    attachments: Mapped[list["MessageAttachment"]] = relationship(
        back_populates="message", lazy="noload", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_messages_chat_id_created", "chat_id", "created_at"),
        Index("ix_messages_chat_id_id", "chat_id", "id"),
        Index("ix_messages_chat_not_deleted", "chat_id", "id", 
              postgresql_where="is_deleted = false"),
        Index("ix_messages_chat_created_not_deleted", 
              "chat_id", "created_at",
              postgresql_where="is_deleted = false"),
    )

    @classmethod
    def create(
        cls,
        sender_id: int | None,
        chat_id: int,
        content: str | None,
        reply_to_id: int | None = None,
        message_type: MessageType = MessageType.TEXT,
        forwarded_from_chat_id: int | None = None,
        forwarded_from_message_id: int | None = None,
    ) -> Self:
        if message_type == MessageType.REPLY and reply_to_id is None:
            raise ValueError("reply_to_id is required for REPLY messages")

        instance = cls(
            author_id=sender_id,
            chat_id=chat_id,
            content=content,
            reply_to_id=reply_to_id,
            type=message_type,
            forwarded_from_chat_id=forwarded_from_chat_id,
            forwarded_from_message_id=forwarded_from_message_id,
        )

        if message_type != MessageType.SYSTEM and content:
            instance.validate_content()
        return instance

    def update_content(self, new_content: str, modified_by: int) -> None:
        self.content = new_content
        self.is_edited = True
        self.validate_content()
        self.register_event(
            ModifiedMessageEvent(
                self.id, new_content, self.chat_id, modified_by=modified_by
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
        if not self.content:
            return

        assert isinstance(self.content, str)

        if len(self.content) > chat_config.MAX_MESSAGE_LENGTH:
            raise MessageTooLongException(
                length=len(self.content),
                max_length=chat_config.MAX_MESSAGE_LENGTH
            )

        self.content = escape(self.content, quote=True)

        if self.content is not None and '\x00' in self.content:  # type: ignore
            raise ValueError("Null bytes not allowed")
