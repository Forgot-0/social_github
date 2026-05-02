from dataclasses import dataclass
from datetime import datetime
from enum import Enum as PyEnum
from typing import Self
from uuid import UUID as PyUUID, uuid7

from sqlalchemy import UUID, BigInteger, Boolean, DateTime, Enum, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.config import chat_config
from app.chats.exceptions import AccessDeniedChatException, MemberLimitExceededException, SlowModeOutOfRangeException
from app.chats.models.chat_members import ChatMember
from app.chats.models.message import Message
from app.core.db.base_model import BaseModel, DateMixin, SoftDeleteMixin
from app.core.events.event import BaseEvent


class ChatType(str, PyEnum):
    DIRECT = "direct"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class ChatFanoutStrategy(str, PyEnum):
    FANOUT_ON_WRITE = "fanout_on_write"
    ACTIVE_SUBSCRIBERS = "active_subscribers"
    CHANNEL_SUBSCRIBERS = "channel_subscribers"


@dataclass(frozen=True)
class CreatedChatEvent(BaseEvent):
    chat_id: str
    created_by: int
    name: str | None
    member_ids: list[int]
    chat_type: str
    member_count: int

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
    admin_only: bool
    slow_mode_seconds: int
    permissions: dict[str, bool]

    __event_name__ = "chats.chat.updated"

    def get_partition_key(self) -> str:
        return str(self.chat_id)


@dataclass(frozen=True)
class DeletedChatEvent(BaseEvent):
    chat_id: str
    deleted_by: int

    __event_name__ = "chats.chat.deleted"

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
class BannedChatMemberEvent(BaseEvent):
    chat_id: str
    requester_id: int
    target_user_id: int
    ban: bool

    __event_name__ = "chats.member.banned"

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

    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    seq_counter: Mapped[int] = mapped_column(BigInteger, default=0)

    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)
    name: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(String(1024))
    avatar_s3_key: Mapped[str | None] = mapped_column(String(512))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0)

    admin_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    slow_mode_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    permissions: Mapped[dict[str, bool]] = mapped_column(JSONB, server_default="{}", default=dict)

    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    members: Mapped[list["ChatMember"]] = relationship(back_populates="chat", lazy="noload")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", foreign_keys=[Message.chat_id], lazy="noload")

    __table_args__ = (
        Index("ix_chats_type_public", "type", "is_public"),
        Index("ix_chats_last_activity", "last_activity_at"),
        Index("ix_chats_type_member_count", "type", "member_count"),
    )

    @staticmethod
    def member_limit(chat_type: ChatType) -> int:
        if chat_type == ChatType.DIRECT:
            return 2
        if chat_type == ChatType.GROUP:
            return chat_config.MAX_GROUP_MEMBERS
        if chat_type == ChatType.SUPERGROUP:
            return chat_config.MAX_SUPERGROUP_MEMBERS
        if chat_type == ChatType.CHANNEL:
            return chat_config.MAX_CHANNEL_SUBSCRIBERS
        return chat_config.MAX_MEMBERS

    @property
    def fanout_strategy(self) -> ChatFanoutStrategy:
        if self.type == ChatType.CHANNEL:
            return ChatFanoutStrategy.CHANNEL_SUBSCRIBERS
        if self.type == ChatType.SUPERGROUP:
            return ChatFanoutStrategy.ACTIVE_SUBSCRIBERS
        if self.type == ChatType.GROUP and self.member_count > chat_config.FAN_OUT_WRITE_THRESHOLD:
            return ChatFanoutStrategy.ACTIVE_SUBSCRIBERS
        return ChatFanoutStrategy.FANOUT_ON_WRITE

    @classmethod
    def create(
        cls,
        created_by: int,
        members_ids: list[int],
        chat_type: ChatType = ChatType.DIRECT,
        name: str | None = None,
        description: str | None = None,
        is_public: bool = False,
        admin_only: bool = False,
        slow_mode_seconds: int = 0,
        permissions: dict[str, bool] | None = None,
    ) -> Self:
        members_ids = list(dict.fromkeys(int(member_id) for member_id in members_ids if int(member_id) != created_by))

        if chat_type == ChatType.DIRECT and len(members_ids) != 1:
            raise MemberLimitExceededException(limit=2)

        participant_count = len(members_ids) + 1
        limit = cls.member_limit(chat_type)
        if participant_count > limit:
            raise MemberLimitExceededException(limit=limit)

        cls._validate_slow_mode(slow_mode_seconds)

        instance = cls(
            id=uuid7(),
            created_by=created_by,
            type=chat_type,
            name=name,
            description=description,
            is_public=is_public,
            admin_only=admin_only,
            slow_mode_seconds=slow_mode_seconds,
            permissions=permissions or {},
        )

        if chat_type == ChatType.DIRECT:
            instance.add_member(created_by, role_id=4)
            instance.add_member(members_ids[0], role_id=4)

        elif chat_type == ChatType.GROUP:
            instance.add_member(created_by, role_id=1)
            for m_id in members_ids:
                instance.add_member(m_id, role_id=5)

        elif chat_type == ChatType.SUPERGROUP:
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
                member_ids=members_ids,
                chat_type=chat_type.value,
                member_count=instance.member_count,
            )
        )

        return instance

    def update(
        self,
        updated_by: int,
        name: str | None,
        description: str | None,
        is_public: bool | None,
        admin_only: bool | None = None,
        slow_mode_seconds: int | None = None,
        permissions: dict[str, bool] | None = None,
    ) -> None:
        if slow_mode_seconds is not None:
            self._validate_slow_mode(slow_mode_seconds)
            self.slow_mode_seconds = slow_mode_seconds
        if admin_only is not None:
            self.admin_only = admin_only
        if permissions is not None:
            self.permissions = permissions

        self.name = name
        self.description = description
        if is_public is not None:
            self.is_public = is_public

        self.register_event(
            UpdatedChatEvent(
                chat_id=str(self.id),
                updated_by=updated_by,
                name=self.name,
                description=self.description,
                is_public=self.is_public,
                admin_only=self.admin_only,
                slow_mode_seconds=self.slow_mode_seconds,
                permissions=self.permissions or {},
            )
        )

    def delete(self, deleted_by: int) -> None:
        self.soft_delete()
        self.register_event(
            DeletedChatEvent(
                chat_id=str(self.id),
                deleted_by=deleted_by,
            )
        )

    def add_member(self, member_id: int, role_id: int) -> None:
        limit = self.member_limit(self.type)
        if self.member_count >= limit:
            raise MemberLimitExceededException(limit=limit)

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
            raise AccessDeniedChatException(chat_id=str(self.id), requester_id=user_id)

        self.member_count -= 1
        self.register_event(LeftChatMemberEvent(
            chat_id=str(self.id),
            user_id=user_id,
        ))

    def kick_member(self, target: int, requester_id: int) -> None:
        if target == requester_id:
            raise AccessDeniedChatException(chat_id=str(self.id), requester_id=requester_id)
        self.member_count -= 1
        self.register_event(KickedChatMemberEvent(
            chat_id=str(self.id),
            requester_id=requester_id,
            target_user_id=target
        ))

    def ban_member(self, target: int, requester_id: int, ban: bool) -> None:
        if target == requester_id:
            raise AccessDeniedChatException(chat_id=str(self.id), requester_id=requester_id)
        self.register_event(BannedChatMemberEvent(
            chat_id=str(self.id),
            requester_id=requester_id,
            target_user_id=target,
            ban=ban,
        ))

    def update_last_activity(self, message_date: datetime) -> None:
        self.last_activity_at = message_date

    @staticmethod
    def _validate_slow_mode(slow_mode_seconds: int) -> None:
        if slow_mode_seconds < 0 or slow_mode_seconds > chat_config.MAX_SLOW_MODE_SECONDS:
            raise SlowModeOutOfRangeException(seconds=slow_mode_seconds)
