from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.rooms.models.room_member import RoomMemer


class Room(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "rooms"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=True, primary_key=True)

    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    members: Mapped[list["RoomMemer"]] = relationship("RoomMemer", back_populates="room")
