from typing import Self

from sqlalchemy import BigInteger, Boolean, String, Text
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
    )

    @classmethod
    def create(
        cls, name: str, slug: str,
        created_by: int, description: str | None=None,
        is_public: bool=True, chat_id: int | None=None,
    ) -> Self:
        instance = cls(
            name=name,
            slug=slug,
            created_by=created_by,
            description=description,
            is_public=is_public,
            chat_id=chat_id
        )

        return instance

    def add_memeber(self, member_id: int, username: str, role_id: int) -> None:
        self.members.append(
            RoomMember(
                user_id=member_id,
                username=username,
                role_id=role_id,
                is_muted=False
            )
        )

    def get_member_by_id(self, memebr_id: int) -> RoomMember | None:
        for member in self.members:
            if member.user_id == memebr_id:
                return member



class RoomBan(BaseModel, DateMixin):
    __tablename__ = "room_bans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_slug: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    banned_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    room: Mapped["Room"] = relationship("Room", back_populates="bans")
