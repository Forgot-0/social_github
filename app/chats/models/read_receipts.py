from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import UUID, BigInteger, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin


class ReadReceipt(BaseModel, DateMixin):
    __tablename__ = "read_receipts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[PyUUID] = mapped_column(
        UUID, ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    last_read_message_seq: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_read_receipt"),
    )
