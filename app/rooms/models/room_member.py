from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin
from app.rooms.models.role_chat import RoomRole
from app.rooms.models.rooms import Room


class RoomMemer(BaseModel, DateMixin):
    __tablename__ = "room_members"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("room_roles.id"), nullable=False)
    room_slug: Mapped[str] = mapped_column(String, ForeignKey("rooms.slug"), nullable=False)

    role: Mapped["RoomRole"] = relationship("RoomRole")
    room: Mapped["Room"] = relationship("Room", back_populates="members")

