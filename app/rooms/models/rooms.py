from typing import Self

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.rooms.models.room_member import RoomMember


class Room(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "rooms"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, primary_key=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    members: Mapped[list["RoomMember"]] = relationship(
        "RoomMember",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    bans: Mapped[list["RoomBan"]] = relationship(
        "RoomBan",
        back_populates="room",
        cascade="all, delete-orphan",
        foreign_keys="[RoomBan.room_slug]",
    )

    @classmethod
    def create(
        cls,
        name: str,
        slug: str,
        created_by: int,
        description: str | None = None,
        is_public: bool = True,
        chat_id: int | None = None,
    ) -> Self:
        return cls(
            name=name,
            slug=slug,
            created_by=created_by,
            description=description,
            is_public=is_public,
            chat_id=chat_id,
        )

    def add_memeber(self, member_id: int, username: str, role_id: int) -> RoomMember:
        member = RoomMember(
            user_id=member_id,
            username=username,
            role_id=role_id,
            is_muted=False,
        )
        self.members.append(member)
        return member

    def get_member_by_id(self, member_id: int) -> RoomMember | None:
        for member in self.members:
            if member.user_id == member_id:
                return member
        return None

    @property
    def member_count(self) -> int:
        return len(self.members)


class RoomBan(BaseModel, DateMixin):
    __tablename__ = "room_bans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_slug: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("rooms.slug", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    banned_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    room: Mapped["Room"] = relationship(
        "Room",
        back_populates="bans",
        foreign_keys=[room_slug],
    )