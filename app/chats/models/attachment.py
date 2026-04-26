from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Self
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import UUID, BigInteger, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin

if TYPE_CHECKING:
    from app.chats.models.message import Message


class AttachmentType(str, PyEnum):
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"

class AttachmentStatus(str, PyEnum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"

class MessageAttachment(BaseModel, DateMixin):
    __tablename__ = "message_attachments"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    chat_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    uploader_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    attachment_type: Mapped[AttachmentType] = mapped_column(
        Enum(AttachmentType), nullable=False
    )
    attachment_status: Mapped[AttachmentStatus] = mapped_column(
        Enum(AttachmentStatus), nullable=False
    )

    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    message: Mapped["Message"] = relationship(back_populates="attachments", lazy="noload")

    __table_args__ = (
        Index("ix_msg_attachments_message_id", "message_id"),
        Index("ix_msg_attachments_chat_uploader", "chat_id", "uploader_id"),
    )

    @classmethod
    def create(
        cls, chat_id: UUID, uploader_id: int,
        attachment_type: AttachmentType, s3_key: str, mime_type: str,
        original_filename: str, size: int,
    ) -> Self:
        instance = cls(
            id=uuid4(),
            chat_id=chat_id,
            message_id=None, uploader_id=uploader_id,
            attachment_type=attachment_type, s3_key=s3_key, mime_type=mime_type,
            original_filename=original_filename, size=size,
            attachment_status=AttachmentStatus.PENDING
        )
        return instance

    def set_resolution(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def set_duration(self, duration_seconds: int) -> None:
        self.duration_seconds =duration_seconds

    def mark_proccesed(self) -> None:
        self.attachment_status = AttachmentStatus.SUCCESS
