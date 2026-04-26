from dataclasses import dataclass
from datetime import datetime
from enum import Enum as PyEnum
from typing import Self
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import UUID, BigInteger, Boolean, DateTime, Enum, Index, Integer, String
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
class CreatedChatEvent(BaseEvent):
    chat_id: str
    created_by: int
    name: str | None
    member_ids: list[int]

    __event_name__ = "chats.chat.created"

    def get_partition_key(self) -> str:
        return str(self.chat_id)


@dataclass(frozen=True)
class UpdatedChatEvent(BaseEvent):
    chat_id: str
    updated_by: int
    name: str | None
    description: str | None
    is_public: bool

    __event_name__ = "chats.chat.updated"

    def get_partition_key(self) -> str:
        return str(self.chat_id)

@dataclass(frozen=True)
class AddedChatMemberEvent(BaseEvent):
    chat_id: str
    user_id: int
    role_id: int

    __event_name__ = "chats.member.added"

    def get_partition_key(self) -> str:
        return str(self.chat_id)


@dataclass(frozen=True)
class KickedChatMemberEvent(BaseEvent):
    chat_id: str
    requester_id: int
    target_user_id: int

    __event_name__ = "chats.member.kicked"

    def get_partition_key(self) -> str:
        return str(self.chat_id)


@dataclass(frozen=True)
class LeftChatMemberEvent(BaseEvent):
    chat_id: str
    user_id: int

    __event_name__ = "chats.member.left"

    def get_partition_key(self) -> str:
        return str(self.chat_id)


class Chat(BaseModel, DateMixin, SoftDeleteMixin):
    __tablename__ = "chats"

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, autoincrement=True)
    seq_counter:Mapped[int] = mapped_column(BigInteger, default=0)

    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)
    name: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(String(1024))
    avatar_s3_key: Mapped[str | None] = mapped_column(String(512))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=2)

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
            id=uuid4(),
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

        instance.register_event(
            CreatedChatEvent(
                chat_id=str(instance.id),
                created_by=created_by,
                name=name,
                member_ids=members_ids
            )
        )

        return instance

    def update(self, updated_by: int, name: str | None, description: str | None, is_public: bool) -> None:
        self.name = name
        self.description = description
        self.is_public = is_public
        self.register_event(
            UpdatedChatEvent(
                chat_id=str(self.id),
                updated_by=updated_by,
                name=name,
                description=description,
                is_public=is_public
            )
        )

    def add_member(self, member_id: int, role_id: int) -> None:
        self.members.append(
            ChatMember(
                user_id=member_id,
                role_id=role_id,
            )
        )
        self.member_count += 1
        self.register_event(
            AddedChatMemberEvent(
                chat_id=str(self.id),
                user_id=member_id,
                role_id=role_id,
            )
        )

    def leave(self, user_id: int) -> None:
        if self.created_by == user_id:
            raise

        self.member_count -= 1
        self.register_event(LeftChatMemberEvent(
            chat_id=str(self.id),
            user_id=user_id,
        ))

    def update_last_activity(self, message_id: int, message_date: datetime) -> None:
        if self.last_activity_at is not None and self.last_activity_at > message_date:
            return

        self.last_activity_at = message_date
