from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional
from uuid import UUID as PyUUID

from sqlalchemy import UUID, BigInteger, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin

if TYPE_CHECKING:
    from app.chats.models.message import Message


class AttachmentType(str, PyEnum):
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"


class MessageAttachment(BaseModel, DateMixin):
    __tablename__ = "message_attachments"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploader_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    attachment_type: Mapped[AttachmentType] = mapped_column(
        Enum(AttachmentType), nullable=False
    )
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    message: Mapped["Message"] = relationship(back_populates="attachments", lazy="noload")

    __table_args__ = (
        Index("ix_msg_attachments_message_id", "message_id"),
        Index("ix_msg_attachments_chat_uploader", "chat_id", "uploader_id"),
    )
