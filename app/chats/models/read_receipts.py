from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin


class ReadReceipt(BaseModel, DateMixin):
    __tablename__ = "read_receipts"
    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_read_receipt"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    last_read_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)


