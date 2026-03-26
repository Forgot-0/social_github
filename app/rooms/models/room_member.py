from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel, DateMixin
from app.rooms.models.role_chat import RoomRole

if TYPE_CHECKING:
    from app.rooms.models.rooms import Room


class RoomMember(BaseModel, DateMixin):
    __tablename__ = "room_members"
    __table_args__ = (
        UniqueConstraint("room_slug", "user_id", name="uq_room_member"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("room_roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    room_slug: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("rooms.slug", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permissions_overrides: Mapped[dict[str, bool]] = mapped_column(JSONB, server_default="{}")

    role: Mapped["RoomRole"] = relationship("RoomRole", lazy="joined")
    room: Mapped["Room"] = relationship("Room", back_populates="members")


    def effective_permissions(self) -> dict[str, bool]:
        perms = self.role.permissions.copy()
        if self.permissions_overrides:
            perms.update(self.permissions_overrides)
        return perms
