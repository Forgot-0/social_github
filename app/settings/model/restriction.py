from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Enum as SAEnum,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin



class BlockReason(StrEnum):
    PERSONAL = "personal"
    SPAM = "spam"
    ABUSE = "abuse"
    OTHER = "other"


class BlockedUser(BaseModel, DateMixin):
    __tablename__ = "blocked_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    blocker_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True,
        comment="Кто заблокировал",
    )
    blocked_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True,
        comment="Кого заблокировали",
    )
    reason: Mapped[BlockReason | None] = mapped_column(
        SAEnum(BlockReason), nullable=True,
    )
    note: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
        comment="Личная заметка пользователя о причине блокировки",
    )

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_blocked_users"),
    )



class MutedUser(BaseModel, DateMixin):
    __tablename__ = "muted_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True,
        comment="Кто заглушил",
    )
    muted_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Кого заглушили", index=True
    )
    muted_until: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True,
        comment="Unix timestamp до которого заглушён; null = навсегда",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "muted_id", name="uq_muted_users"),
    )
