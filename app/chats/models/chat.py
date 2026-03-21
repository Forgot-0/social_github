from dataclasses import dataclass
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Self

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.config import chat_config
from app.chats.exceptions import MemberLimitExceededException
from app.chats.models.chat_members import ChatMember, MemberRole
from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.core.events.event import BaseEvent

if TYPE_CHECKING:
    from app.chats.models.message import Message



class ChatType(str, PyEnum):
    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"


@dataclass(frozen=True)
class KickedChatMemberEvent(BaseEvent):
    chat_id: int
    requester_id: int
    target_user_id: int


@dataclass(frozen=True)
class LeavedChatMemberEvent(BaseEvent):
    chat_id: int
    user_id: int


class Chat(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)
    name: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(String(1024))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    last_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    members:  Mapped[list["ChatMember"]] = relationship(back_populates="chat", lazy="noload")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat",  lazy="noload")

    __table_args__ = (
        Index("ix_chats_type_public", "type", "is_public"),
        Index("ix_chats_last_activity", "last_activity_at"),
    )


    @classmethod
    def create(
        cls,
        created_by: int,
        members_ids: list[int],
        chat_type: ChatType = ChatType.DIRECT,
        name: str | None = None,
        description: str | None = None,
        is_public: bool = False,
    ) -> Self:
        instance = cls(
            created_by=created_by,
            type=chat_type,
            name=name,
            description=description,
            is_public=is_public
        )

        if chat_type == ChatType.DIRECT:
            if len(members_ids) != 1:
                raise MemberLimitExceededException(limit=2)

            instance.add_member(created_by)
            instance.add_member(members_ids[0])
        
        elif chat_type == ChatType.GROUP:
            if len(members_ids) > chat_config.MAX_MEMEBERS:
                raise MemberLimitExceededException(limit=chat_config.MAX_MEMEBERS)

            instance.add_member(created_by, role=MemberRole.OWNER)
            for m_id in members_ids:
                instance.add_member(m_id)


        return instance


    def add_member(self, member_id: int, role: MemberRole=MemberRole.MEMBER) -> None:
        self.members.append(
            ChatMember(
                user_id=member_id,
                role=role,
            )
        )

    def update_last_activity(self,  message_id: int, message_date: datetime) -> None:
        if self.last_activity_at == message_id:
            raise

        self.last_message_id = message_id
        self.last_activity_at = message_date

