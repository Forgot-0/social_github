from dataclasses import dataclass
from datetime import datetime
from enum import Enum as PyEnum
from typing import Self

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.config import chat_config
from app.chats.exceptions import MemberLimitExceededException
from app.chats.models.chat_members import ChatMember
from app.chats.models.message import Message
from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.core.events.event import BaseEvent


class ChatType(str, PyEnum):
    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"


@dataclass(frozen=True)
class CreadtedChatEvent(BaseEvent):
    chat_id: int
    created_by: int
    name: str | None
    member_ids: list[int]

    __event_name__ = "chat.created"


@dataclass(frozen=True)
class AddedChatMemberEvent(BaseEvent):
    chat_id: int
    user_id: int
    role_id: int

    __event_name__ = "chat.memebers.added"


@dataclass(frozen=True)
class KickedChatMemberEvent(BaseEvent):
    chat_id: int
    requester_id: int
    target_user_id: int

    __event_name__ = "chat.memebers.kicked"


@dataclass(frozen=True)
class LeavedChatMemberEvent(BaseEvent):
    chat_id: int
    user_id: int
    username: str = ""

    __event_name__ = "chat.memebers.leaved"


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

    members: Mapped[list["ChatMember"]] = relationship(back_populates="chat", lazy="noload")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", foreign_keys=[Message.chat_id], lazy="noload")

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
        if len(members_ids) > chat_config.MAX_MEMBERS:
            raise MemberLimitExceededException(limit=chat_config.MAX_MEMBERS)

        instance = cls(
            created_by=created_by,
            type=chat_type,
            name=name,
            description=description,
            is_public=is_public,
        )

        if chat_type == ChatType.DIRECT:
            if len(members_ids) != 1:
                raise MemberLimitExceededException(limit=2)
            instance.add_member(created_by, 4)
            instance.add_member(members_ids[0], 4)

        elif chat_type == ChatType.GROUP:
            instance.add_member(created_by, role_id=1)
            for m_id in members_ids:
                instance.add_member(m_id, role_id=5)

        elif chat_type == ChatType.CHANNEL:
            instance.add_member(created_by, role_id=1)
            for m_id in members_ids:
                instance.add_member(m_id, role_id=6)

        return instance

    def add_member(self, member_id: int, role_id: int) -> None:
        self.members.append(
            ChatMember(
                user_id=member_id,
                role_id=role_id,
            )
        )
        self.register_event(
            AddedChatMemberEvent(
                chat_id=self.id,
                user_id=member_id,
                role_id=role_id,
            )
        )

    def update_last_activity(self, message_id: int, message_date: datetime) -> None:
        if self.last_activity_at is not None and self.last_activity_at > message_date:
            return

        self.last_message_id = message_id
        self.last_activity_at = message_date
