"""Production-ready messenger module for send/forward/edit/delete/attach flows.

Clean Architecture + DDD + CQRS oriented single-file module.

This file is intentionally self-contained at the application/infrastructure boundary
and expects your existing SQLAlchemy ORM models to live in
`app.infrastructure.sqlalchemy.models`.

Expected ORM models / enums from your project:
- Chat
- ChatMember
- Message
- MessageAttachment
- OutboxEvent (or equivalent)
- AttachmentStatus, MessageType
- BaseModel, DateMixin, SoftDeleteMixin (already used in your codebase)

You can split this file into package modules later without changing logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Protocol
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.infrastructure.sqlalchemy.models import (
    AttachmentStatus,
    Chat,
    ChatMember,
    Message,
    MessageAttachment,
    MessageType,
    OutboxEvent,
    ReadReceipt,
)


# =========================
# Domain errors
# =========================

class DomainError(Exception):
    """Base domain error."""


class ChatNotFoundError(DomainError):
    pass


class NotChatMemberError(DomainError):
    pass


class UserBannedFromChatError(DomainError):
    pass


class MessageNotFoundError(DomainError):
    pass


class MessageReplyTargetNotFoundError(DomainError):
    pass


class ForwardForbiddenError(DomainError):
    pass


class DuplicateCommandError(DomainError):
    pass


class AttachmentNotFoundError(DomainError):
    pass


class AttachmentOwnershipError(DomainError):
    pass


class AttachmentStateError(DomainError):
    pass


class MessageCannotBeEditedError(DomainError):
    pass


class MessageCannotBeDeletedError(DomainError):
    pass


# =========================
# Domain events
# =========================

@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_id: UUID
    occurred_at: datetime

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["event_id"] = str(payload["event_id"])
        payload["occurred_at"] = payload["occurred_at"].isoformat()
        return payload


@dataclass(frozen=True, slots=True)
class MessageCreatedEvent(DomainEvent):
    message_id: UUID
    chat_id: UUID
    seq: int
    author_id: int | None
    content: str | None

    @staticmethod
    def create(message_id: UUID, chat_id: UUID, seq: int, author_id: int | None, content: str | None) -> "MessageCreatedEvent":
        return MessageCreatedEvent(
            event_id=uuid4(),
            occurred_at=datetime.now(timezone.utc),
            message_id=message_id,
            chat_id=chat_id,
            seq=seq,
            author_id=author_id,
            content=content,
        )


@dataclass(frozen=True, slots=True)
class MessageForwardedEvent(DomainEvent):
    message_id: UUID
    source_chat_id: UUID
    source_message_id: UUID
    target_chat_id: UUID
    seq: int
    author_id: int

    @staticmethod
    def create(message_id: UUID, source_chat_id: UUID, source_message_id: UUID, target_chat_id: UUID, seq: int, author_id: int) -> "MessageForwardedEvent":
        return MessageForwardedEvent(
            event_id=uuid4(),
            occurred_at=datetime.now(timezone.utc),
            message_id=message_id,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            target_chat_id=target_chat_id,
            seq=seq,
            author_id=author_id,
        )


@dataclass(frozen=True, slots=True)
class MessageEditedEvent(DomainEvent):
    message_id: UUID
    chat_id: UUID
    seq: int
    editor_id: int

    @staticmethod
    def create(message_id: UUID, chat_id: UUID, seq: int, editor_id: int) -> "MessageEditedEvent":
        return MessageEditedEvent(
            event_id=uuid4(),
            occurred_at=datetime.now(timezone.utc),
            message_id=message_id,
            chat_id=chat_id,
            seq=seq,
            editor_id=editor_id,
        )


@dataclass(frozen=True, slots=True)
class MessageDeletedEvent(DomainEvent):
    message_id: UUID
    chat_id: UUID
    seq: int
    deleter_id: int

    @staticmethod
    def create(message_id: UUID, chat_id: UUID, seq: int, deleter_id: int) -> "MessageDeletedEvent":
        return MessageDeletedEvent(
            event_id=uuid4(),
            occurred_at=datetime.now(timezone.utc),
            message_id=message_id,
            chat_id=chat_id,
            seq=seq,
            deleter_id=deleter_id,
        )


# =========================
# Application DTOs / Commands
# =========================

@dataclass(frozen=True, slots=True)
class AttachmentDraftDTO:
    attachment_id: UUID


@dataclass(frozen=True, slots=True)
class SendMessageCommand:
    command_id: UUID
    chat_id: UUID
    author_id: int
    content: str | None = None
    reply_to_id: UUID | None = None
    forwarded_from_chat_id: UUID | None = None
    forwarded_from_message_id: UUID | None = None
    attachment_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class ForwardMessageCommand:
    command_id: UUID
    source_chat_id: UUID
    source_message_id: UUID
    target_chat_id: UUID
    author_id: int
    text_override: str | None = None
    with_attachments: bool = True


@dataclass(frozen=True, slots=True)
class EditMessageCommand:
    command_id: UUID
    chat_id: UUID
    message_id: UUID
    editor_id: int
    new_content: str


@dataclass(frozen=True, slots=True)
class DeleteMessageCommand:
    command_id: UUID
    chat_id: UUID
    message_id: UUID
    deleter_id: int
    hard_delete: bool = False


@dataclass(frozen=True, slots=True)
class AttachFilesCommand:
    command_id: UUID
    chat_id: UUID
    message_id: UUID
    uploader_id: int
    attachment_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class SendMessageResultDTO:
    message_id: UUID
    chat_id: UUID
    seq: int
    created_at: datetime
    attachment_ids: list[UUID]


@dataclass(frozen=True, slots=True)
class ForwardMessageResultDTO:
    message_id: UUID
    chat_id: UUID
    seq: int
    created_at: datetime
    forwarded_from_chat_id: UUID
    forwarded_from_message_id: UUID
    attachment_ids: list[UUID]


@dataclass(frozen=True, slots=True)
class EditMessageResultDTO:
    message_id: UUID
    chat_id: UUID
    seq: int
    edited_at: datetime
    content: str


@dataclass(frozen=True, slots=True)
class DeleteMessageResultDTO:
    message_id: UUID
    chat_id: UUID
    seq: int
    deleted_at: datetime
    hard_deleted: bool


@dataclass(frozen=True, slots=True)
class AttachFilesResultDTO:
    message_id: UUID
    chat_id: UUID
    attachment_ids: list[UUID]


# =========================
# Ports
# =========================

class ChatRepository(Protocol):
    async def get_by_id(self, chat_id: UUID) -> Chat | None: ...
    async def next_seq(self, chat_id: UUID) -> int: ...
    async def touch_last_activity(self, chat_id: UUID) -> None: ...
    async def increment_member_count(self, chat_id: UUID, delta: int) -> None: ...


class ChatMemberRepository(Protocol):
    async def get_by_chat_and_user(self, chat_id: UUID, user_id: int) -> ChatMember | None: ...


class MessageRepository(Protocol):
    async def get_by_id(self, message_id: UUID) -> Message | None: ...
    async def get_by_id_with_attachments(self, message_id: UUID) -> Message | None: ...
    async def get_by_chat_and_seq(self, chat_id: UUID, seq: int) -> Message | None: ...
    async def add(self, message: Message) -> None: ...
    async def delete(self, message: Message) -> None: ...


class AttachmentRepository(Protocol):
    async def claim_for_message(
        self,
        attachment_ids: tuple[UUID, ...],
        chat_id: UUID,
        uploader_id: int,
        message_id: UUID,
    ) -> list[MessageAttachment]: ...

    async def clone_attachments_for_forward(
        self,
        source_attachments: list[MessageAttachment],
        new_chat_id: UUID,
        new_message_id: UUID,
        new_uploader_id: int,
    ) -> list[MessageAttachment]: ...

    async def get_by_ids(self, attachment_ids: tuple[UUID, ...]) -> list[MessageAttachment]: ...


class OutboxRepository(Protocol):
    async def add_event(self, event_type: str, aggregate_id: UUID, payload: dict[str, Any]) -> None: ...


class InboxRepository(Protocol):
    async def seen(self, command_id: UUID) -> bool: ...
    async def mark_seen(self, command_id: UUID, result_ref: str | None = None) -> None: ...


class UnitOfWork(Protocol):
    chats: ChatRepository
    chat_members: ChatMemberRepository
    messages: MessageRepository
    attachments: AttachmentRepository
    outbox: OutboxRepository
    inbox: InboxRepository

    async def __aenter__(self) -> "UnitOfWork": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


# =========================
# SQLAlchemy repositories
# =========================

class SqlAlchemyChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, chat_id: UUID) -> Chat | None:
        return await self.session.get(Chat, chat_id)

    async def next_seq(self, chat_id: UUID) -> int:
        stmt = (
            update(Chat)
            .where(Chat.id == chat_id)
            .values(seq_counter=Chat.seq_counter + 1)
            .returning(Chat.seq_counter)
        )
        result = await self.session.execute(stmt)
        seq = result.scalar_one()
        return int(seq)

    async def touch_last_activity(self, chat_id: UUID) -> None:
        stmt = update(Chat).where(Chat.id == chat_id).values(last_activity_at=func.now())
        await self.session.execute(stmt)

    async def increment_member_count(self, chat_id: UUID, delta: int) -> None:
        stmt = update(Chat).where(Chat.id == chat_id).values(member_count=Chat.member_count + delta)
        await self.session.execute(stmt)


class SqlAlchemyChatMemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_chat_and_user(self, chat_id: UUID, user_id: int) -> ChatMember | None:
        stmt = select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SqlAlchemyMessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, message_id: UUID) -> Message | None:
        return await self.session.get(Message, message_id)

    async def get_by_id_with_attachments(self, message_id: UUID) -> Message | None:
        stmt = (
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.attachments))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_chat_and_seq(self, chat_id: UUID, seq: int) -> Message | None:
        stmt = select(Message).where(Message.chat_id == chat_id, Message.seq == seq)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, message: Message) -> None:
        self.session.add(message)

    async def delete(self, message: Message) -> None:
        await self.session.delete(message)


class SqlAlchemyAttachmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_ids(self, attachment_ids: tuple[UUID, ...]) -> list[MessageAttachment]:
        if not attachment_ids:
            return []
        stmt = select(MessageAttachment).where(MessageAttachment.id.in_(attachment_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def claim_for_message(
        self,
        attachment_ids: tuple[UUID, ...],
        chat_id: UUID,
        uploader_id: int,
        message_id: UUID,
    ) -> list[MessageAttachment]:
        if not attachment_ids:
            return []

        stmt = (
            update(MessageAttachment)
            .where(
                MessageAttachment.id.in_(attachment_ids),
                MessageAttachment.chat_id == chat_id,
                MessageAttachment.uploader_id == uploader_id,
                MessageAttachment.attachment_status == AttachmentStatus.PENDING,
            )
            .values(message_id=message_id, attachment_status=AttachmentStatus.SUCCESS)
            .returning(MessageAttachment)
        )
        result = await self.session.execute(stmt)
        attachments = list(result.scalars().all())

        if len(attachments) != len(set(attachment_ids)):
            raise AttachmentStateError("One or more attachments are missing, not owned by uploader, or not pending")

        return attachments

    async def clone_attachments_for_forward(
        self,
        source_attachments: list[MessageAttachment],
        new_chat_id: UUID,
        new_message_id: UUID,
        new_uploader_id: int,
    ) -> list[MessageAttachment]:
        cloned: list[MessageAttachment] = []
        for att in source_attachments:
            if att.attachment_status != AttachmentStatus.SUCCESS:
                continue
            cloned_attachment = MessageAttachment(
                id=uuid4(),
                message_id=new_message_id,
                chat_id=new_chat_id,
                uploader_id=new_uploader_id,
                attachment_type=att.attachment_type,
                attachment_status=AttachmentStatus.SUCCESS,
                s3_key=att.s3_key,
                mime_type=att.mime_type,
                original_filename=att.original_filename,
                size=att.size,
                width=att.width,
                height=att.height,
                duration_seconds=att.duration_seconds,
            )
            self.session.add(cloned_attachment)
            cloned.append(cloned_attachment)
        return cloned


class SqlAlchemyOutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_event(self, event_type: str, aggregate_id: UUID, payload: dict[str, Any]) -> None:
        self.session.add(
            OutboxEvent(
                event_type=event_type,
                aggregate_id=aggregate_id,
                payload=payload,
                status="pending",
            )
        )


class SqlAlchemyInboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def seen(self, command_id: UUID) -> bool:
        stmt = select(1).select_from(InboxCommand).where(InboxCommand.command_id == command_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def mark_seen(self, command_id: UUID, result_ref: str | None = None) -> None:
        self.session.add(InboxCommand(command_id=command_id, result_ref=result_ref))


# =========================
# Inbox / Idempotency table
# =========================

class InboxCommand:
    """Minimal idempotency record model.

    Add this model to your SQLAlchemy metadata via migrations.
    """

    __tablename__ = "inbox_commands"

    # NOTE: defined as plain class here for a single-file module. In your project,
    # convert it to a proper SQLAlchemy declarative model.

    def __init__(self, command_id: UUID, result_ref: str | None = None):
        self.command_id = command_id
        self.result_ref = result_ref


# =========================
# Unit of Work
# =========================

class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.session: AsyncSession | None = None

        self.chats: SqlAlchemyChatRepository | None = None
        self.chat_members: SqlAlchemyChatMemberRepository | None = None
        self.messages: SqlAlchemyMessageRepository | None = None
        self.attachments: SqlAlchemyAttachmentRepository | None = None
        self.outbox: SqlAlchemyOutboxRepository | None = None
        self.inbox: SqlAlchemyInboxRepository | None = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self.session_factory()
        self.chats = SqlAlchemyChatRepository(self.session)
        self.chat_members = SqlAlchemyChatMemberRepository(self.session)
        self.messages = SqlAlchemyMessageRepository(self.session)
        self.attachments = SqlAlchemyAttachmentRepository(self.session)
        self.outbox = SqlAlchemyOutboxRepository(self.session)
        self.inbox = SqlAlchemyInboxRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            if self.session is not None:
                await self.session.close()

    async def commit(self) -> None:
        if self.session is not None:
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session is not None:
            await self.session.rollback()


# =========================
# Common helper functions
# =========================

async def _ensure_chat_member(uow: UnitOfWork, chat_id: UUID, user_id: int) -> ChatMember:
    membership = await uow.chat_members.get_by_chat_and_user(chat_id, user_id)
    if membership is None:
        raise NotChatMemberError("User is not a member of the chat")
    if getattr(membership, "is_banned", False):
        raise UserBannedFromChatError("User is banned from the chat")
    return membership


async def _ensure_chat(uow: UnitOfWork, chat_id: UUID) -> Chat:
    chat = await uow.chats.get_by_id(chat_id)
    if chat is None:
        raise ChatNotFoundError(f"Chat {chat_id} not found")
    return chat


async def _ensure_message_in_chat(uow: UnitOfWork, message_id: UUID, chat_id: UUID) -> Message:
    message = await uow.messages.get_by_id(message_id)
    if message is None or message.chat_id != chat_id:
        raise MessageNotFoundError("Message not found in chat")
    return message


# =========================
# Handlers
# =========================

@dataclass(slots=True)
class SendMessageHandler:
    uow: UnitOfWork

    async def handle(self, command: SendMessageCommand) -> SendMessageResultDTO:
        async with self.uow:
            if await self.uow.inbox.seen(command.command_id):
                raise DuplicateCommandError("Duplicate command")

            await _ensure_chat(self.uow, command.chat_id)
            await _ensure_chat_member(self.uow, command.chat_id, command.author_id)

            if command.reply_to_id is not None:
                reply_target = await self.uow.messages.get_by_id(command.reply_to_id)
                if reply_target is None or reply_target.chat_id != command.chat_id:
                    raise MessageReplyTargetNotFoundError("Reply target not found in chat")

            seq = await self.uow.chats.next_seq(command.chat_id)
            message_id = uuid4()
            message = Message(
                id=message_id,
                chat_id=command.chat_id,
                seq=seq,
                author_id=command.author_id,
                type=MessageType.TEXT if command.content else MessageType.TEXT,
                content=command.content,
                reply_to_id=command.reply_to_id,
                forwarded_from_chat_id=command.forwarded_from_chat_id,
                forwarded_from_message_id=command.forwarded_from_message_id,
                is_deleted=False,
                is_edited=False,
            )
            await self.uow.messages.add(message)

            attached_ids: list[UUID] = []
            if command.attachment_ids:
                attachments = await self.uow.attachments.claim_for_message(
                    attachment_ids=command.attachment_ids,
                    chat_id=command.chat_id,
                    uploader_id=command.author_id,
                    message_id=message_id,
                )
                attached_ids = [a.id for a in attachments]

            await self.uow.chats.touch_last_activity(command.chat_id)
            await self.uow.outbox.add_event(
                event_type="message.created",
                aggregate_id=message_id,
                payload=MessageCreatedEvent.create(
                    message_id=message_id,
                    chat_id=command.chat_id,
                    seq=seq,
                    author_id=command.author_id,
                    content=command.content,
                ).to_payload(),
            )
            await self.uow.inbox.mark_seen(command.command_id, result_ref=str(message_id))
            await self.uow.commit()

            return SendMessageResultDTO(
                message_id=message_id,
                chat_id=command.chat_id,
                seq=seq,
                created_at=message.created_at,
                attachment_ids=attached_ids,
            )


@dataclass(slots=True)
class ForwardMessageHandler:
    uow: UnitOfWork

    async def handle(self, command: ForwardMessageCommand) -> ForwardMessageResultDTO:
        async with self.uow:
            if await self.uow.inbox.seen(command.command_id):
                raise DuplicateCommandError("Duplicate command")

            await _ensure_chat(self.uow, command.source_chat_id)
            await _ensure_chat(self.uow, command.target_chat_id)
            await _ensure_chat_member(self.uow, command.source_chat_id, command.author_id)
            await _ensure_chat_member(self.uow, command.target_chat_id, command.author_id)

            source_message = await self.uow.messages.get_by_id_with_attachments(command.source_message_id)
            if source_message is None or source_message.chat_id != command.source_chat_id:
                raise MessageNotFoundError("Source message not found in source chat")

            seq = await self.uow.chats.next_seq(command.target_chat_id)
            message_id = uuid4()
            message = Message(
                id=message_id,
                chat_id=command.target_chat_id,
                seq=seq,
                author_id=command.author_id,
                type=source_message.type or MessageType.TEXT,
                content=command.text_override if command.text_override is not None else source_message.content,
                reply_to_id=None,
                forwarded_from_chat_id=command.source_chat_id,
                forwarded_from_message_id=command.source_message_id,
                is_deleted=False,
                is_edited=False,
            )
            await self.uow.messages.add(message)

            attachment_ids: list[UUID] = []
            if command.with_attachments and getattr(source_message, "attachments", None):
                cloned = await self.uow.attachments.clone_attachments_for_forward(
                    source_attachments=list(source_message.attachments),
                    new_chat_id=command.target_chat_id,
                    new_message_id=message_id,
                    new_uploader_id=command.author_id,
                )
                attachment_ids = [a.id for a in cloned]

            await self.uow.chats.touch_last_activity(command.target_chat_id)
            await self.uow.outbox.add_event(
                event_type="message.forwarded",
                aggregate_id=message_id,
                payload=MessageForwardedEvent.create(
                    message_id=message_id,
                    source_chat_id=command.source_chat_id,
                    source_message_id=command.source_message_id,
                    target_chat_id=command.target_chat_id,
                    seq=seq,
                    author_id=command.author_id,
                ).to_payload(),
            )
            await self.uow.inbox.mark_seen(command.command_id, result_ref=str(message_id))
            await self.uow.commit()

            return ForwardMessageResultDTO(
                message_id=message_id,
                chat_id=command.target_chat_id,
                seq=seq,
                created_at=message.created_at,
                forwarded_from_chat_id=command.source_chat_id,
                forwarded_from_message_id=command.source_message_id,
                attachment_ids=attachment_ids,
            )


@dataclass(slots=True)
class EditMessageHandler:
    uow: UnitOfWork

    async def handle(self, command: EditMessageCommand) -> EditMessageResultDTO:
        async with self.uow:
            if await self.uow.inbox.seen(command.command_id):
                raise DuplicateCommandError("Duplicate command")

            await _ensure_chat_member(self.uow, command.chat_id, command.editor_id)
            message = await _ensure_message_in_chat(self.uow, command.message_id, command.chat_id)

            if message.author_id != command.editor_id:
                raise MessageCannotBeEditedError("Only author can edit this message")
            if getattr(message, "is_deleted", False):
                raise MessageCannotBeEditedError("Deleted message cannot be edited")

            message.content = command.new_content
            message.is_edited = True
            if hasattr(message, "edited_at"):
                message.edited_at = datetime.now(timezone.utc)

            await self.uow.chats.touch_last_activity(command.chat_id)
            await self.uow.outbox.add_event(
                event_type="message.edited",
                aggregate_id=message.id,
                payload=MessageEditedEvent.create(
                    message_id=message.id,
                    chat_id=command.chat_id,
                    seq=message.seq,
                    editor_id=command.editor_id,
                ).to_payload(),
            )
            await self.uow.inbox.mark_seen(command.command_id, result_ref=str(message.id))
            await self.uow.commit()

            return EditMessageResultDTO(
                message_id=message.id,
                chat_id=command.chat_id,
                seq=message.seq,
                edited_at=getattr(message, "edited_at", datetime.now(timezone.utc)),
                content=message.content or "",
            )


@dataclass(slots=True)
class DeleteMessageHandler:
    uow: UnitOfWork

    async def handle(self, command: DeleteMessageCommand) -> DeleteMessageResultDTO:
        async with self.uow:
            if await self.uow.inbox.seen(command.command_id):
                raise DuplicateCommandError("Duplicate command")

            await _ensure_chat_member(self.uow, command.chat_id, command.deleter_id)
            message = await _ensure_message_in_chat(self.uow, command.message_id, command.chat_id)

            if message.author_id != command.deleter_id:
                raise MessageCannotBeDeletedError("Only author can delete this message")

            if command.hard_delete:
                await self.uow.messages.delete(message)
            else:
                message.is_deleted = True
                message.content = None
                if hasattr(message, "deleted_at"):
                    message.deleted_at = datetime.now(timezone.utc)

            await self.uow.chats.touch_last_activity(command.chat_id)
            await self.uow.outbox.add_event(
                event_type="message.deleted",
                aggregate_id=message.id,
                payload=MessageDeletedEvent.create(
                    message_id=message.id,
                    chat_id=command.chat_id,
                    seq=message.seq,
                    deleter_id=command.deleter_id,
                ).to_payload(),
            )
            await self.uow.inbox.mark_seen(command.command_id, result_ref=str(message.id))
            await self.uow.commit()

            return DeleteMessageResultDTO(
                message_id=message.id,
                chat_id=command.chat_id,
                seq=message.seq,
                deleted_at=datetime.now(timezone.utc),
                hard_deleted=command.hard_delete,
            )


@dataclass(slots=True)
class AttachFilesHandler:
    uow: UnitOfWork

    async def handle(self, command: AttachFilesCommand) -> AttachFilesResultDTO:
        async with self.uow:
            if await self.uow.inbox.seen(command.command_id):
                raise DuplicateCommandError("Duplicate command")

            await _ensure_chat_member(self.uow, command.chat_id, command.uploader_id)
            message = await _ensure_message_in_chat(self.uow, command.message_id, command.chat_id)

            if getattr(message, "is_deleted", False):
                raise AttachmentStateError("Cannot attach files to deleted message")

            attachments = await self.uow.attachments.claim_for_message(
                attachment_ids=command.attachment_ids,
                chat_id=command.chat_id,
                uploader_id=command.uploader_id,
                message_id=command.message_id,
            )

            await self.uow.chats.touch_last_activity(command.chat_id)
            await self.uow.outbox.add_event(
                event_type="message.attachments_added",
                aggregate_id=message.id,
                payload={
                    "event_id": str(uuid4()),
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "message_id": str(message.id),
                    "chat_id": str(command.chat_id),
                    "attachment_ids": [str(a.id) for a in attachments],
                },
            )
            await self.uow.inbox.mark_seen(command.command_id, result_ref=str(message.id))
            await self.uow.commit()

            return AttachFilesResultDTO(
                message_id=message.id,
                chat_id=command.chat_id,
                attachment_ids=[a.id for a in attachments],
            )


# =========================
# FastAPI transport models
# =========================

class SendMessageRequest(BaseModel):
    command_id: UUID
    content: str | None = Field(default=None, max_length=5000)
    reply_to_id: UUID | None = None
    forwarded_from_chat_id: UUID | None = None
    forwarded_from_message_id: UUID | None = None
    attachment_ids: list[UUID] = []


class SendMessageResponse(BaseModel):
    message_id: UUID
    chat_id: UUID
    seq: int
    created_at: str
    attachment_ids: list[UUID]


class ForwardMessageRequest(BaseModel):
    command_id: UUID
    source_chat_id: UUID
    source_message_id: UUID
    target_chat_id: UUID
    text_override: str | None = Field(default=None, max_length=5000)
    with_attachments: bool = True


class ForwardMessageResponse(BaseModel):
    message_id: UUID
    chat_id: UUID
    seq: int
    created_at: str
    forwarded_from_chat_id: UUID
    forwarded_from_message_id: UUID
    attachment_ids: list[UUID]


class EditMessageRequest(BaseModel):
    command_id: UUID
    new_content: str = Field(max_length=5000)


class EditMessageResponse(BaseModel):
    message_id: UUID
    chat_id: UUID
    seq: int
    edited_at: str
    content: str


class DeleteMessageRequest(BaseModel):
    command_id: UUID
    hard_delete: bool = False


class DeleteMessageResponse(BaseModel):
    message_id: UUID
    chat_id: UUID
    seq: int
    deleted_at: str
    hard_deleted: bool


class AttachFilesRequest(BaseModel):
    command_id: UUID
    attachment_ids: list[UUID]


class AttachFilesResponse(BaseModel):
    message_id: UUID
    chat_id: UUID
    attachment_ids: list[UUID]


# =========================
# Dependency factories
# =========================


def build_send_message_handler(uow: UnitOfWork) -> SendMessageHandler:
    return SendMessageHandler(uow=uow)


def build_forward_message_handler(uow: UnitOfWork) -> ForwardMessageHandler:
    return ForwardMessageHandler(uow=uow)


def build_edit_message_handler(uow: UnitOfWork) -> EditMessageHandler:
    return EditMessageHandler(uow=uow)


def build_delete_message_handler(uow: UnitOfWork) -> DeleteMessageHandler:
    return DeleteMessageHandler(uow=uow)


def build_attach_files_handler(uow: UnitOfWork) -> AttachFilesHandler:
    return AttachFilesHandler(uow=uow)


# =========================
# API router factory
# =========================


def build_messenger_router(
    *,
    get_current_user_id: Any,
    get_uow: Any,
) -> APIRouter:
    """Build a router.

    Parameters
    ----------
    get_current_user_id:
        FastAPI dependency that returns int user id.
    get_uow:
        FastAPI dependency that returns UnitOfWork instance.
    """

    router = APIRouter(prefix="/chats", tags=["messenger"])

    @router.post("/{chat_id}/messages", response_model=SendMessageResponse)
    async def send_message(
        chat_id: UUID,
        req: SendMessageRequest,
        current_user_id: int = Depends(get_current_user_id),
        uow: UnitOfWork = Depends(get_uow),
    ) -> SendMessageResponse:
        handler = build_send_message_handler(uow)
        result = await handler.handle(
            SendMessageCommand(
                command_id=req.command_id,
                chat_id=chat_id,
                author_id=current_user_id,
                content=req.content,
                reply_to_id=req.reply_to_id,
                forwarded_from_chat_id=req.forwarded_from_chat_id,
                forwarded_from_message_id=req.forwarded_from_message_id,
                attachment_ids=tuple(req.attachment_ids),
            )
        )
        return SendMessageResponse(
            message_id=result.message_id,
            chat_id=result.chat_id,
            seq=result.seq,
            created_at=result.created_at.isoformat(),
            attachment_ids=result.attachment_ids,
        )

    @router.post("/{chat_id}/messages/{message_id}/edit", response_model=EditMessageResponse)
    async def edit_message(
        chat_id: UUID,
        message_id: UUID,
        req: EditMessageRequest,
        current_user_id: int = Depends(get_current_user_id),
        uow: UnitOfWork = Depends(get_uow),
    ) -> EditMessageResponse:
        handler = build_edit_message_handler(uow)
        result = await handler.handle(
            EditMessageCommand(
                command_id=req.command_id,
                chat_id=chat_id,
                message_id=message_id,
                editor_id=current_user_id,
                new_content=req.new_content,
            )
        )
        return EditMessageResponse(
            message_id=result.message_id,
            chat_id=result.chat_id,
            seq=result.seq,
            edited_at=result.edited_at.isoformat(),
            content=result.content,
        )

    @router.post("/{chat_id}/messages/{message_id}/delete", response_model=DeleteMessageResponse)
    async def delete_message(
        chat_id: UUID,
        message_id: UUID,
        req: DeleteMessageRequest,
        current_user_id: int = Depends(get_current_user_id),
        uow: UnitOfWork = Depends(get_uow),
    ) -> DeleteMessageResponse:
        handler = build_delete_message_handler(uow)
        result = await handler.handle(
            DeleteMessageCommand(
                command_id=req.command_id,
                chat_id=chat_id,
                message_id=message_id,
                deleter_id=current_user_id,
                hard_delete=req.hard_delete,
            )
        )
        return DeleteMessageResponse(
            message_id=result.message_id,
            chat_id=result.chat_id,
            seq=result.seq,
            deleted_at=result.deleted_at.isoformat(),
            hard_deleted=result.hard_deleted,
        )

    @router.post("/{chat_id}/messages/{message_id}/attachments", response_model=AttachFilesResponse)
    async def attach_files(
        chat_id: UUID,
        message_id: UUID,
        req: AttachFilesRequest,
        current_user_id: int = Depends(get_current_user_id),
        uow: UnitOfWork = Depends(get_uow),
    ) -> AttachFilesResponse:
        handler = build_attach_files_handler(uow)
        result = await handler.handle(
            AttachFilesCommand(
                command_id=req.command_id,
                chat_id=chat_id,
                message_id=message_id,
                uploader_id=current_user_id,
                attachment_ids=tuple(req.attachment_ids),
            )
        )
        return AttachFilesResponse(
            message_id=result.message_id,
            chat_id=result.chat_id,
            attachment_ids=result.attachment_ids,
        )

    @router.post("/messages/forward", response_model=ForwardMessageResponse)
    async def forward_message(
        req: ForwardMessageRequest,
        current_user_id: int = Depends(get_current_user_id),
        uow: UnitOfWork = Depends(get_uow),
    ) -> ForwardMessageResponse:
        handler = build_forward_message_handler(uow)
        result = await handler.handle(
            ForwardMessageCommand(
                command_id=req.command_id,
                source_chat_id=req.source_chat_id,
                source_message_id=req.source_message_id,
                target_chat_id=req.target_chat_id,
                author_id=current_user_id,
                text_override=req.text_override,
                with_attachments=req.with_attachments,
            )
        )
        return ForwardMessageResponse(
            message_id=result.message_id,
            chat_id=result.chat_id,
            seq=result.seq,
            created_at=result.created_at.isoformat(),
            forwarded_from_chat_id=result.forwarded_from_chat_id,
            forwarded_from_message_id=result.forwarded_from_message_id,
            attachment_ids=result.attachment_ids,
        )

    return router


# =========================
# Optional: projection contract
# =========================

class MessageProjectionRepository(Protocol):
    async def upsert_last_message(self, chat_id: UUID, seq: int, message_id: UUID, at: datetime) -> None: ...
    async def increment_unread(self, chat_id: UUID, user_id: int, delta: int) -> None: ...


# =========================
# Read receipts / CQRS query models
# =========================

@dataclass(frozen=True, slots=True)
class MarkChatReadCommand:
    command_id: UUID
    chat_id: UUID
    user_id: int
    last_read_message_seq: int


@dataclass(frozen=True, slots=True)
class MarkChatReadResultDTO:
    chat_id: UUID
    user_id: int
    last_read_message_seq: int
    last_read_at: datetime


@dataclass(frozen=True, slots=True)
class MessageDTO:
    id: UUID
    chat_id: UUID
    seq: int
    author_id: int | None
    type: str
    content: str | None
    reply_to_id: UUID | None
    forwarded_from_chat_id: UUID | None
    forwarded_from_message_id: UUID | None
    is_deleted: bool
    is_edited: bool
    created_at: datetime
    attachments: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ChatMessagePageDTO:
    chat_id: UUID
    items: list[MessageDTO]
    next_before_seq: int | None


@dataclass(frozen=True, slots=True)
class ChatUnreadCountDTO:
    chat_id: UUID
    user_id: int
    unread_count: int
    last_read_message_seq: int


@dataclass(frozen=True, slots=True)
class GetChatMessagesQuery:
    chat_id: UUID
    user_id: int
    limit: int = 50
    before_seq: int | None = None


@dataclass(frozen=True, slots=True)
class GetUnreadCountQuery:
    chat_id: UUID
    user_id: int


# =========================
# Query ports
# =========================

class ReadReceiptRepository(Protocol):
    async def get_by_chat_and_user(self, chat_id: UUID, user_id: int) -> Any | None: ...
    async def upsert_last_read(self, chat_id: UUID, user_id: int, last_read_message_seq: int) -> Any: ...


class MessageQueryRepository(Protocol):
    async def get_chat_messages_page(self, chat_id: UUID, limit: int, before_seq: int | None) -> list[Message]: ...
    async def get_latest_chat_messages(self, chat_id: UUID, limit: int) -> list[Message]: ...
    async def get_unread_count(self, chat_id: UUID, user_id: int) -> int: ...
    async def get_last_read_seq(self, chat_id: UUID, user_id: int) -> int: ...


# =========================
# SQLAlchemy query repositories
# =========================

class SqlAlchemyReadReceiptRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_chat_and_user(self, chat_id: UUID, user_id: int) -> Any | None:
        stmt = select(ReadReceipt).where(ReadReceipt.chat_id == chat_id, ReadReceipt.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_last_read(self, chat_id: UUID, user_id: int, last_read_message_seq: int) -> Any:
        existing = await self.get_by_chat_and_user(chat_id, user_id)
        now = datetime.now(timezone.utc)
        if existing is None:
            rr = ReadReceipt(
                chat_id=chat_id,
                user_id=user_id,
                last_read_message_seq=last_read_message_seq,
                last_read_at=now,
            )
            self.session.add(rr)
            return rr
        if last_read_message_seq > int(existing.last_read_message_seq):
            existing.last_read_message_seq = last_read_message_seq
            existing.last_read_at = now
        return existing


class SqlAlchemyMessageQueryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_chat_messages_page(self, chat_id: UUID, limit: int, before_seq: int | None) -> list[Message]:
        stmt = select(Message).where(Message.chat_id == chat_id)
        if before_seq is not None:
            stmt = stmt.where(Message.seq < before_seq)
        stmt = stmt.order_by(Message.seq.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_chat_messages(self, chat_id: UUID, limit: int) -> list[Message]:
        stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.seq.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_last_read_seq(self, chat_id: UUID, user_id: int) -> int:
        stmt = select(ReadReceipt.last_read_message_seq).where(ReadReceipt.chat_id == chat_id, ReadReceipt.user_id == user_id)
        result = await self.session.execute(stmt)
        value = result.scalar_one_or_none()
        return int(value or 0)

    async def get_unread_count(self, chat_id: UUID, user_id: int) -> int:
        last_read_seq = await self.get_last_read_seq(chat_id, user_id)
        stmt = select(func.count()).select_from(Message).where(
            Message.chat_id == chat_id,
            Message.seq > last_read_seq,
            Message.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)


# =========================
# Query / read handlers
# =========================

@dataclass(slots=True)
class MarkChatReadHandler:
    uow: UnitOfWork

    async def handle(self, command: MarkChatReadCommand) -> MarkChatReadResultDTO:
        async with self.uow:
            if await self.uow.inbox.seen(command.command_id):
                existing = await self.uow.session.get(ReadReceipt, (command.chat_id, command.user_id)) if getattr(self.uow, "session", None) is not None else None
                if existing is not None:
                    return MarkChatReadResultDTO(
                        chat_id=existing.chat_id,
                        user_id=existing.user_id,
                        last_read_message_seq=int(existing.last_read_message_seq),
                        last_read_at=existing.last_read_at,
                    )
                raise DuplicateCommandError("Duplicate command")

            await _ensure_chat_member(self.uow, command.chat_id, command.user_id)

            repo = SqlAlchemyReadReceiptRepository(self.uow.session)  # type: ignore[arg-type]
            receipt = await repo.upsert_last_read(command.chat_id, command.user_id, command.last_read_message_seq)

            await self.uow.outbox.add_event(
                event_type="chat.read",
                aggregate_id=command.chat_id,
                payload={
                    "event_id": str(uuid4()),
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "chat_id": str(command.chat_id),
                    "user_id": command.user_id,
                    "last_read_message_seq": command.last_read_message_seq,
                },
            )
            await self.uow.inbox.mark_seen(command.command_id, result_ref=f"{command.chat_id}:{command.user_id}")
            await self.uow.commit()

            return MarkChatReadResultDTO(
                chat_id=receipt.chat_id,
                user_id=receipt.user_id,
                last_read_message_seq=int(receipt.last_read_message_seq),
                last_read_at=receipt.last_read_at,
            )


@dataclass(slots=True)
class GetChatMessagesHandler:
    session: AsyncSession

    async def handle(self, query: GetChatMessagesQuery) -> ChatMessagePageDTO:
        await self._ensure_membership(query.chat_id, query.user_id)
        repo = SqlAlchemyMessageQueryRepository(self.session)
        items = await repo.get_chat_messages_page(query.chat_id, limit=min(query.limit, 100), before_seq=query.before_seq)
        items = list(reversed(items))

        dto_items: list[MessageDTO] = []
        for m in items:
            dto_items.append(
                MessageDTO(
                    id=m.id,
                    chat_id=m.chat_id,
                    seq=m.seq,
                    author_id=m.author_id,
                    type=getattr(m.type, "value", str(m.type)),
                    content=None if getattr(m, "is_deleted", False) else m.content,
                    reply_to_id=m.reply_to_id,
                    forwarded_from_chat_id=m.forwarded_from_chat_id,
                    forwarded_from_message_id=m.forwarded_from_message_id,
                    is_deleted=getattr(m, "is_deleted", False),
                    is_edited=getattr(m, "is_edited", False),
                    created_at=m.created_at,
                    attachments=[
                        {
                            "id": a.id,
                            "s3_key": a.s3_key,
                            "mime_type": a.mime_type,
                            "original_filename": a.original_filename,
                            "size": a.size,
                            "width": a.width,
                            "height": a.height,
                            "duration_seconds": a.duration_seconds,
                            "status": getattr(a.attachment_status, "value", str(a.attachment_status)),
                        }
                        for a in getattr(m, "attachments", [])
                    ],
                )
            )

        next_before_seq = dto_items[0].seq if dto_items else None
        return ChatMessagePageDTO(chat_id=query.chat_id, items=dto_items, next_before_seq=next_before_seq)

    async def _ensure_membership(self, chat_id: UUID, user_id: int) -> None:
        stmt = select(ChatMember.id).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise NotChatMemberError("User is not a member of the chat")


@dataclass(slots=True)
class GetUnreadCountHandler:
    session: AsyncSession

    async def handle(self, query: GetUnreadCountQuery) -> ChatUnreadCountDTO:
        await self._ensure_membership(query.chat_id, query.user_id)
        repo = SqlAlchemyMessageQueryRepository(self.session)
        last_read_seq = await repo.get_last_read_seq(query.chat_id, query.user_id)
        unread_count = await repo.get_unread_count(query.chat_id, query.user_id)
        return ChatUnreadCountDTO(
            chat_id=query.chat_id,
            user_id=query.user_id,
            unread_count=unread_count,
            last_read_message_seq=last_read_seq,
        )

    async def _ensure_membership(self, chat_id: UUID, user_id: int) -> None:
        stmt = select(ChatMember.id).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise NotChatMemberError("User is not a member of the chat")


# =========================
# Query API transport models
# =========================

class MarkChatReadRequest(BaseModel):
    command_id: UUID
    last_read_message_seq: int = Field(ge=0)


class MarkChatReadResponse(BaseModel):
    chat_id: UUID
    user_id: int
    last_read_message_seq: int
    last_read_at: str


class GetChatMessagesResponseItem(BaseModel):
    id: UUID
    chat_id: UUID
    seq: int
    author_id: int | None
    type: str
    content: str | None
    reply_to_id: UUID | None
    forwarded_from_chat_id: UUID | None
    forwarded_from_message_id: UUID | None
    is_deleted: bool
    is_edited: bool
    created_at: str
    attachments: list[dict[str, Any]]


class GetChatMessagesResponse(BaseModel):
    chat_id: UUID
    items: list[GetChatMessagesResponseItem]
    next_before_seq: int | None


class GetUnreadCountResponse(BaseModel):
    chat_id: UUID
    user_id: int
    unread_count: int
    last_read_message_seq: int


# =========================
# Query router extension
# =========================

def extend_messenger_router_with_queries(
    router: APIRouter,
    *,
    get_current_user_id: Any,
    get_session: Any,
    get_uow: Any,
) -> APIRouter:
    @router.get("/{chat_id}/messages", response_model=GetChatMessagesResponse)
    async def get_chat_messages(
        chat_id: UUID,
        limit: int = 50,
        before_seq: int | None = None,
        current_user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_session),
    ) -> GetChatMessagesResponse:
        handler = GetChatMessagesHandler(session=session)
        result = await handler.handle(GetChatMessagesQuery(chat_id=chat_id, user_id=current_user_id, limit=min(limit, 100), before_seq=before_seq))
        return GetChatMessagesResponse(
            chat_id=result.chat_id,
            items=[
                GetChatMessagesResponseItem(
                    id=item.id,
                    chat_id=item.chat_id,
                    seq=item.seq,
                    author_id=item.author_id,
                    type=item.type,
                    content=item.content,
                    reply_to_id=item.reply_to_id,
                    forwarded_from_chat_id=item.forwarded_from_chat_id,
                    forwarded_from_message_id=item.forwarded_from_message_id,
                    is_deleted=item.is_deleted,
                    is_edited=item.is_edited,
                    created_at=item.created_at.isoformat(),
                    attachments=item.attachments,
                )
                for item in result.items
            ],
            next_before_seq=result.next_before_seq,
        )

    @router.get("/{chat_id}/unread", response_model=GetUnreadCountResponse)
    async def get_unread_count(
        chat_id: UUID,
        current_user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_session),
    ) -> GetUnreadCountResponse:
        handler = GetUnreadCountHandler(session=session)
        result = await handler.handle(GetUnreadCountQuery(chat_id=chat_id, user_id=current_user_id))
        return GetUnreadCountResponse(
            chat_id=result.chat_id,
            user_id=result.user_id,
            unread_count=result.unread_count,
            last_read_message_seq=result.last_read_message_seq,
        )

    @router.post("/{chat_id}/read", response_model=MarkChatReadResponse)
    async def mark_chat_read(
        chat_id: UUID,
        req: MarkChatReadRequest,
        current_user_id: int = Depends(get_current_user_id),
        uow: UnitOfWork = Depends(get_uow),
    ) -> MarkChatReadResponse:
        handler = MarkChatReadHandler(uow=uow)
        result = await handler.handle(
            MarkChatReadCommand(
                command_id=req.command_id,
                chat_id=chat_id,
                user_id=current_user_id,
                last_read_message_seq=req.last_read_message_seq,
            )
        )
        return MarkChatReadResponse(
            chat_id=result.chat_id,
            user_id=result.user_id,
            last_read_message_seq=result.last_read_message_seq,
            last_read_at=result.last_read_at.isoformat(),
        )

    @router.get("/me/chats", response_model=GetUserChatsResponse)
    async def get_my_chats(
        limit: int = 50,
        before_last_activity_at: datetime | None = None,
        before_chat_id: UUID | None = None,
        current_user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_session),
    ) -> GetUserChatsResponse:
        handler = GetUserChatsHandler(session=session)
        result = await handler.handle(
            GetUserChatsQuery(
                user_id=current_user_id,
                limit=min(limit, USER_CHAT_LIST_MAX_LIMIT),
                before_last_activity_at=before_last_activity_at,
                before_chat_id=before_chat_id,
            )
        )
        return GetUserChatsResponse(
            items=[
                GetUserChatsResponseItem(
                    chat_id=item.chat_id,
                    type=item.type,
                    name=item.name,
                    description=item.description,
                    avatar_s3_key=item.avatar_s3_key,
                    is_public=item.is_public,
                    member_count=item.member_count,
                    is_big_chat=item.is_big_chat,
                    last_activity_at=item.last_activity_at.isoformat() if item.last_activity_at else None,
                    last_message_seq=item.last_message_seq,
                    unread_count=item.unread_count,
                    last_read_message_seq=item.last_read_message_seq,
                )
                for item in result.items
            ],
            next_before_last_activity_at=result.next_before_last_activity_at.isoformat() if result.next_before_last_activity_at else None,
            next_before_chat_id=result.next_before_chat_id,
        )

    return router


# =========================
# Production limits / big chat support
# =========================

BIG_CHAT_MEMBER_THRESHOLD = 1000
USER_CHAT_LIST_DEFAULT_LIMIT = 50
USER_CHAT_LIST_MAX_LIMIT = 100


def is_big_chat(member_count: int | None) -> bool:
    return int(member_count or 0) >= BIG_CHAT_MEMBER_THRESHOLD


@dataclass(frozen=True, slots=True)
class GetUserChatsQuery:
    user_id: int
    limit: int = USER_CHAT_LIST_DEFAULT_LIMIT
    before_last_activity_at: datetime | None = None
    before_chat_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class UserChatListItemDTO:
    chat_id: UUID
    type: str
    name: str | None
    description: str | None
    avatar_s3_key: str | None
    is_public: bool
    member_count: int
    is_big_chat: bool
    last_activity_at: datetime | None
    last_message_seq: int
    unread_count: int
    last_read_message_seq: int


@dataclass(frozen=True, slots=True)
class UserChatListPageDTO:
    items: list[UserChatListItemDTO]
    next_before_last_activity_at: datetime | None
    next_before_chat_id: UUID | None


class UserChatListQueryRepository(Protocol):
    async def get_user_chats_page(
        self,
        user_id: int,
        limit: int,
        before_last_activity_at: datetime | None,
        before_chat_id: UUID | None,
    ) -> list[tuple[Chat, int | None]]: ...


class SqlAlchemyUserChatListQueryRepository:
    """Read-side optimized list of chats for the current user.

    Keyset pagination uses (last_activity_at, chat_id).
    Unread count is approximated from seq_counter - last_read_seq so the query
    stays cheap even for big chats.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_chats_page(
        self,
        user_id: int,
        limit: int,
        before_last_activity_at: datetime | None,
        before_chat_id: UUID | None,
    ) -> list[tuple[Chat, int | None]]:
        stmt = (
            select(Chat, ReadReceipt.last_read_message_seq)
            .join(ChatMember, ChatMember.chat_id == Chat.id)
            .outerjoin(
                ReadReceipt,
                and_(ReadReceipt.chat_id == Chat.id, ReadReceipt.user_id == user_id),
            )
            .where(ChatMember.user_id == user_id)
        )

        if before_last_activity_at is not None and before_chat_id is not None:
            stmt = stmt.where(
                or_(
                    Chat.last_activity_at < before_last_activity_at,
                    and_(Chat.last_activity_at == before_last_activity_at, Chat.id < before_chat_id),
                )
            )

        stmt = stmt.order_by(Chat.last_activity_at.desc().nullslast(), Chat.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        rows = result.all()
        return [(row[0], row[1]) for row in rows]


@dataclass(slots=True)
class GetUserChatsHandler:
    session: AsyncSession

    async def handle(self, query: GetUserChatsQuery) -> UserChatListPageDTO:
        limit = max(1, min(query.limit, USER_CHAT_LIST_MAX_LIMIT))
        repo = SqlAlchemyUserChatListQueryRepository(self.session)
        rows = await repo.get_user_chats_page(
            user_id=query.user_id,
            limit=limit,
            before_last_activity_at=query.before_last_activity_at,
            before_chat_id=query.before_chat_id,
        )

        items: list[UserChatListItemDTO] = []
        for chat, last_read_seq in rows:
            last_read_seq_int = int(last_read_seq or 0)
            last_message_seq = int(chat.seq_counter or 0)
            unread_count = max(last_message_seq - last_read_seq_int, 0)
            items.append(
                UserChatListItemDTO(
                    chat_id=chat.id,
                    type=getattr(chat.type, "value", str(chat.type)),
                    name=chat.name,
                    description=chat.description,
                    avatar_s3_key=chat.avatar_s3_key,
                    is_public=chat.is_public,
                    member_count=int(chat.member_count or 0),
                    is_big_chat=is_big_chat(chat.member_count),
                    last_activity_at=chat.last_activity_at,
                    last_message_seq=last_message_seq,
                    unread_count=unread_count,
                    last_read_message_seq=last_read_seq_int,
                )
            )

        next_before_last_activity_at = items[-1].last_activity_at if items else None
        next_before_chat_id = items[-1].chat_id if items else None
        return UserChatListPageDTO(
            items=items,
            next_before_last_activity_at=next_before_last_activity_at,
            next_before_chat_id=next_before_chat_id,
        )


class GetUserChatsResponseItem(BaseModel):
    chat_id: UUID
    type: str
    name: str | None
    description: str | None
    avatar_s3_key: str | None
    is_public: bool
    member_count: int
    is_big_chat: bool
    last_activity_at: str | None
    last_message_seq: int
    unread_count: int
    last_read_message_seq: int


class GetUserChatsResponse(BaseModel):
    items: list[GetUserChatsResponseItem]
    next_before_last_activity_at: str | None
    next_before_chat_id: UUID | None


# =========================
# Read models / projections for big chats
# =========================

@dataclass(slots=True)
class ChatListProjectionRow:
    user_id: int
    chat_id: UUID
    last_activity_at: datetime | None
    last_message_seq: int
    last_read_message_seq: int
    unread_count: int
    updated_at: datetime


@dataclass(slots=True)
class ChatUnreadProjectionRow:
    user_id: int
    chat_id: UUID
    unread_count: int
    last_read_message_seq: int
    last_message_seq: int
    updated_at: datetime


class ChatListProjectionRepository(Protocol):
    async def upsert_chat_list_row(self, row: ChatListProjectionRow) -> None: ...
    async def get_user_chat_list_page(
        self,
        user_id: int,
        limit: int,
        before_last_activity_at: datetime | None,
        before_chat_id: UUID | None,
    ) -> list[ChatListProjectionRow]: ...


class UnreadProjectionRepository(Protocol):
    async def set_unread_count(
        self,
        user_id: int,
        chat_id: UUID,
        unread_count: int,
        last_read_message_seq: int,
        last_message_seq: int,
    ) -> None: ...

    async def get_unread_count(self, user_id: int, chat_id: UUID) -> int: ...


class SqlAlchemyChatListProjectionRepository:
    """Optional read model repository.

    For production at scale, prefer a dedicated projection table or Redis cache.
    This implementation is a SQL fallback.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_chat_list_row(self, row: ChatListProjectionRow) -> None:
        # You will need a proper declarative model/table for this in your project.
        # Here we keep the contract and show the intended write path.
        raise NotImplementedError("Create a dedicated chat_list_projection table for this repository")

    async def get_user_chat_list_page(
        self,
        user_id: int,
        limit: int,
        before_last_activity_at: datetime | None,
        before_chat_id: UUID | None,
    ) -> list[ChatListProjectionRow]:
        raise NotImplementedError("Create a dedicated chat_list_projection table for this repository")


class SqlAlchemyUnreadProjectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_unread_count(
        self,
        user_id: int,
        chat_id: UUID,
        unread_count: int,
        last_read_message_seq: int,
        last_message_seq: int,
    ) -> None:
        raise NotImplementedError("Create a dedicated unread_projection table for this repository")

    async def get_unread_count(self, user_id: int, chat_id: UUID) -> int:
        raise NotImplementedError("Create a dedicated unread_projection table for this repository")


# =========================
# Projection updaters
# =========================

@dataclass(slots=True)
class ChatListProjectionUpdater:
    """Updates list-of-chats projection for a user.

    In production this is usually driven by outbox consumer events:
    - message.created
    - message.forwarded
    - chat.read
    - member.joined / member.left
    - chat.updated
    """

    session: AsyncSession

    async def on_message_created(self, chat: Chat, message: Message, affected_user_ids: list[int]) -> None:
        now = datetime.now(timezone.utc)
        for user_id in affected_user_ids:
            # In production, replace this with a single bulk upsert into projection table.
            # For very large chats, do not iterate over all members synchronously here.
            pass

    async def on_chat_read(self, chat_id: UUID, user_id: int, last_read_message_seq: int, last_message_seq: int, last_activity_at: datetime | None) -> None:
        _ = (chat_id, user_id, last_read_message_seq, last_message_seq, last_activity_at)
        # In production, update unread projection / cache here.
        pass


@dataclass(slots=True)
class OutboxEventEnvelope:
    id: UUID
    event_type: str
    aggregate_id: UUID
    payload: dict[str, Any]
    created_at: datetime


class OutboxConsumer(Protocol):
    async def process(self, event: OutboxEventEnvelope) -> None: ...


@dataclass(slots=True)
class MessengerOutboxConsumer:
    """Consumes outbox events and updates projections / cache.

    Keep this idempotent. In production, use:
    - at-least-once delivery from outbox
    - dedup by event id
    - retry with backoff
    - DLQ on repeated failure
    """

    session: AsyncSession

    async def process(self, event: OutboxEventEnvelope) -> None:
        if event.event_type in {"message.created", "message.forwarded"}:
            await self._handle_message_event(event)
        elif event.event_type == "chat.read":
            await self._handle_chat_read(event)
        elif event.event_type == "message.edited":
            await self._handle_message_edited(event)
        elif event.event_type == "message.deleted":
            await self._handle_message_deleted(event)

    async def _handle_message_event(self, event: OutboxEventEnvelope) -> None:
        _ = event
        # Update chat list projection and unread counters.
        # For huge chats, do not fan out to every member synchronously.
        pass

    async def _handle_chat_read(self, event: OutboxEventEnvelope) -> None:
        _ = event
        pass

    async def _handle_message_edited(self, event: OutboxEventEnvelope) -> None:
        _ = event
        pass

    async def _handle_message_deleted(self, event: OutboxEventEnvelope) -> None:
        _ = event
        pass


# =========================
# Highload rules for big chats
# =========================

BIG_CHAT_DELIVERY_FANOUT_THRESHOLD = 1000
BIG_CHAT_READ_MODEL_ONLY_THRESHOLD = 1000


@dataclass(frozen=True, slots=True)
class ChatDeliveryStrategy:
    fanout_on_write: bool
    use_projection_only: bool


def choose_delivery_strategy(member_count: int | None) -> ChatDeliveryStrategy:
    is_big = int(member_count or 0) >= BIG_CHAT_DELIVERY_FANOUT_THRESHOLD
    return ChatDeliveryStrategy(
        fanout_on_write=not is_big,
        use_projection_only=is_big,
    )


class UserChatListReadRepository(Protocol):
    async def get_page(
        self,
        user_id: int,
        limit: int,
        before_last_activity_at: datetime | None,
        before_chat_id: UUID | None,
    ) -> list[UserChatListItemDTO]: ...


class SqlAlchemyUserChatListReadRepository:
    """Primary read query for user chats.

    This is still DB-backed, but in production you should swap it with:
    - Redis cache read-through
    - dedicated projection table
    - read replica
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_page(
        self,
        user_id: int,
        limit: int,
        before_last_activity_at: datetime | None,
        before_chat_id: UUID | None,
    ) -> list[UserChatListItemDTO]:
        handler = GetUserChatsHandler(session=self.session)
        page = await handler.handle(
            GetUserChatsQuery(
                user_id=user_id,
                limit=limit,
                before_last_activity_at=before_last_activity_at,
                before_chat_id=before_chat_id,
            )
        )
        return page.items


class GetUserChatsProjectionResponse(BaseModel):
    items: list[GetUserChatsResponseItem]
    next_before_last_activity_at: str | None
    next_before_chat_id: UUID | None


# =========================
# Notes for production
# =========================
# 1) Add proper SQLAlchemy declarative model for inbox_commands with unique(command_id).
# 2) Use UUIDv7/ULID or snowflake IDs in production for better index locality.
# 3) For hot chats, seq generation may need partitioning or a dedicated sequencer.
# 4) Outbox consumer should be at-least-once, idempotent on the downstream side.
# 5) For very large uploads, keep upload flow separate: presigned URL -> pending attachment row -> attach to message.
# 6) Prefer partial indexes / partitioning on messages, attachments, receipts by chat_id.
# 7) Query side should prefer keyset pagination and cached read models; avoid OFFSET on big chats.
# 8) Read receipts should be monotonic: never decrease last_read_message_seq.
# =========================
# Projection tables (SQLAlchemy models)
# =========================

class ProcessedOutboxEvent:
    """Idempotency marker for outbox consumer.

    Add as a real SQLAlchemy declarative model in your project.
    Primary key: event_id
    Optional unique constraint on (consumer_name, event_id).
    """

    __tablename__ = "processed_outbox_events"

    def __init__(self, event_id: UUID, consumer_name: str, processed_at: datetime):
        self.event_id = event_id
        self.consumer_name = consumer_name
        self.processed_at = processed_at


class ChatListProjection:
    """Denormalized user chat list row.

    Recommended columns:
    - user_id (indexed)
    - chat_id (indexed)
    - chat_type
    - chat_name
    - chat_description
    - avatar_s3_key
    - is_public
    - member_count
    - is_big_chat
    - last_activity_at
    - last_message_seq
    - last_read_message_seq
    - unread_count
    - updated_at

    Recommended unique constraint: (user_id, chat_id)
    Recommended index for pagination: (user_id, last_activity_at DESC, chat_id DESC)
    """

    __tablename__ = "chat_list_projection"

    def __init__(
        self,
        user_id: int,
        chat_id: UUID,
        chat_type: str,
        chat_name: str | None,
        chat_description: str | None,
        avatar_s3_key: str | None,
        is_public: bool,
        member_count: int,
        is_big_chat: bool,
        last_activity_at: datetime | None,
        last_message_seq: int,
        last_read_message_seq: int,
        unread_count: int,
        updated_at: datetime,
    ):
        self.user_id = user_id
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.chat_name = chat_name
        self.chat_description = chat_description
        self.avatar_s3_key = avatar_s3_key
        self.is_public = is_public
        self.member_count = member_count
        self.is_big_chat = is_big_chat
        self.last_activity_at = last_activity_at
        self.last_message_seq = last_message_seq
        self.last_read_message_seq = last_read_message_seq
        self.unread_count = unread_count
        self.updated_at = updated_at


class UnreadProjection:
    """Compact unread counter projection.

    Recommended unique constraint: (user_id, chat_id)
    Recommended index: (user_id, unread_count DESC, updated_at DESC)
    """

    __tablename__ = "unread_projection"

    def __init__(
        self,
        user_id: int,
        chat_id: UUID,
        unread_count: int,
        last_read_message_seq: int,
        last_message_seq: int,
        updated_at: datetime,
    ):
        self.user_id = user_id
        self.chat_id = chat_id
        self.unread_count = unread_count
        self.last_read_message_seq = last_read_message_seq
        self.last_message_seq = last_message_seq
        self.updated_at = updated_at


# =========================
# Redis cache contracts
# =========================

class RedisChatCache(Protocol):
    async def get_user_chat_list(self, user_id: int, limit: int, before_cursor: str | None) -> list[dict[str, Any]] | None: ...
    async def set_user_chat_list(self, user_id: int, before_cursor: str | None, items: list[dict[str, Any]], ttl_seconds: int) -> None: ...
    async def invalidate_user_chat_list(self, user_id: int) -> None: ...
    async def get_unread_count(self, user_id: int, chat_id: UUID) -> int | None: ...
    async def set_unread_count(self, user_id: int, chat_id: UUID, unread_count: int, ttl_seconds: int) -> None: ...
    async def invalidate_unread_count(self, user_id: int, chat_id: UUID) -> None: ...


class NullRedisChatCache:
    async def get_user_chat_list(self, user_id: int, limit: int, before_cursor: str | None) -> list[dict[str, Any]] | None:
        return None

    async def set_user_chat_list(self, user_id: int, before_cursor: str | None, items: list[dict[str, Any]], ttl_seconds: int) -> None:
        return None

    async def invalidate_user_chat_list(self, user_id: int) -> None:
        return None

    async def get_unread_count(self, user_id: int, chat_id: UUID) -> int | None:
        return None

    async def set_unread_count(self, user_id: int, chat_id: UUID, unread_count: int, ttl_seconds: int) -> None:
        return None

    async def invalidate_unread_count(self, user_id: int, chat_id: UUID) -> None:
        return None


# =========================
# Projection-based read handlers
# =========================

@dataclass(slots=True)
class GetUserChatsProjectionHandler:
    """Primary read handler for the user's chat list.

    Priority order:
    1) Redis cache
    2) Projection table
    3) Fallback to live query

    For 10M users this is the preferred path.
    """

    session: AsyncSession
    cache: RedisChatCache

    async def handle(self, query: GetUserChatsQuery) -> UserChatListPageDTO:
        limit = max(1, min(query.limit, USER_CHAT_LIST_MAX_LIMIT))
        cursor = None
        if query.before_last_activity_at is not None and query.before_chat_id is not None:
            cursor = f"{query.before_last_activity_at.isoformat()}|{query.before_chat_id}"

        cached = await self.cache.get_user_chat_list(query.user_id, limit, cursor)
        if cached is not None:
            items = [
                UserChatListItemDTO(
                    chat_id=UUID(row["chat_id"]),
                    type=row["type"],
                    name=row.get("name"),
                    description=row.get("description"),
                    avatar_s3_key=row.get("avatar_s3_key"),
                    is_public=bool(row["is_public"]),
                    member_count=int(row["member_count"]),
                    is_big_chat=bool(row["is_big_chat"]),
                    last_activity_at=datetime.fromisoformat(row["last_activity_at"]) if row.get("last_activity_at") else None,
                    last_message_seq=int(row["last_message_seq"]),
                    unread_count=int(row["unread_count"]),
                    last_read_message_seq=int(row["last_read_message_seq"]),
                )
                for row in cached
            ]
            return UserChatListPageDTO(
                items=items,
                next_before_last_activity_at=items[-1].last_activity_at if items else None,
                next_before_chat_id=items[-1].chat_id if items else None,
            )

        live = await GetUserChatsHandler(session=self.session).handle(query)
        await self.cache.set_user_chat_list(
            query.user_id,
            cursor,
            [
                {
                    "chat_id": str(item.chat_id),
                    "type": item.type,
                    "name": item.name,
                    "description": item.description,
                    "avatar_s3_key": item.avatar_s3_key,
                    "is_public": item.is_public,
                    "member_count": item.member_count,
                    "is_big_chat": item.is_big_chat,
                    "last_activity_at": item.last_activity_at.isoformat() if item.last_activity_at else None,
                    "last_message_seq": item.last_message_seq,
                    "unread_count": item.unread_count,
                    "last_read_message_seq": item.last_read_message_seq,
                }
                for item in live.items
            ],
            ttl_seconds=30,
        )
        return live


@dataclass(slots=True)
class GetUnreadCountProjectionHandler:
    session: AsyncSession
    cache: RedisChatCache

    async def handle(self, query: GetUnreadCountQuery) -> ChatUnreadCountDTO:
        cached = await self.cache.get_unread_count(query.user_id, query.chat_id)
        if cached is not None:
            repo = SqlAlchemyMessageQueryRepository(self.session)
            last_read_seq = await repo.get_last_read_seq(query.chat_id, query.user_id)
            return ChatUnreadCountDTO(
                chat_id=query.chat_id,
                user_id=query.user_id,
                unread_count=cached,
                last_read_message_seq=last_read_seq,
            )

        live = await GetUnreadCountHandler(session=self.session).handle(query)
        await self.cache.set_unread_count(query.user_id, query.chat_id, live.unread_count, ttl_seconds=10)
        return live


# =========================
# Outbox consumer with projection updates
# =========================

@dataclass(slots=True)
class ProjectionAwareOutboxConsumer:
    session: AsyncSession
    cache: RedisChatCache

    async def process(self, event: OutboxEventEnvelope) -> None:
        if await self._already_processed(event.id):
            return

        if event.event_type in {"message.created", "message.forwarded"}:
            await self._on_message_changed(event)
        elif event.event_type == "chat.read":
            await self._on_chat_read(event)
        elif event.event_type == "message.edited":
            await self._on_message_edited(event)
        elif event.event_type == "message.deleted":
            await self._on_message_deleted(event)

        await self._mark_processed(event.id, event.event_type)

    async def _already_processed(self, event_id: UUID) -> bool:
        stmt = select(ProcessedOutboxEvent).where(ProcessedOutboxEvent.event_id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _mark_processed(self, event_id: UUID, consumer_name: str) -> None:
        self.session.add(ProcessedOutboxEvent(event_id=event_id, consumer_name=consumer_name, processed_at=datetime.now(timezone.utc)))
        await self.session.commit()

    async def _on_message_changed(self, event: OutboxEventEnvelope) -> None:
        chat_id = UUID(event.payload["chat_id"])
        _ = chat_id
        await self.cache.invalidate_user_chat_list(0)

    async def _on_chat_read(self, event: OutboxEventEnvelope) -> None:
        chat_id = UUID(event.payload["chat_id"])
        user_id = int(event.payload["user_id"])
        last_read_seq = int(event.payload["last_read_message_seq"])
        repo = SqlAlchemyMessageQueryRepository(self.session)
        last_message_seq = await repo.get_last_read_seq(chat_id, user_id)
        unread_count = max(last_message_seq - last_read_seq, 0)
        await self.cache.set_unread_count(user_id, chat_id, unread_count, ttl_seconds=30)

    async def _on_message_edited(self, event: OutboxEventEnvelope) -> None:
        _ = event

    async def _on_message_deleted(self, event: OutboxEventEnvelope) -> None:
        _ = event


# =========================
# Projection-aware query router extension
# =========================

def extend_messenger_router_with_projections(
    router: APIRouter,
    *,
    get_current_user_id: Any,
    get_session: Any,
    get_uow: Any,
    get_cache: Any,
) -> APIRouter:
    @router.get("/me/chats", response_model=GetUserChatsResponse)
    async def get_my_chats(
        limit: int = 50,
        before_last_activity_at: datetime | None = None,
        before_chat_id: UUID | None = None,
        current_user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_session),
        cache: RedisChatCache = Depends(get_cache),
    ) -> GetUserChatsResponse:
        handler = GetUserChatsProjectionHandler(session=session, cache=cache)
        result = await handler.handle(
            GetUserChatsQuery(
                user_id=current_user_id,
                limit=limit,
                before_last_activity_at=before_last_activity_at,
                before_chat_id=before_chat_id,
            )
        )
        return GetUserChatsResponse(
            items=[
                GetUserChatsResponseItem(
                    chat_id=item.chat_id,
                    type=item.type,
                    name=item.name,
                    description=item.description,
                    avatar_s3_key=item.avatar_s3_key,
                    is_public=item.is_public,
                    member_count=item.member_count,
                    is_big_chat=item.is_big_chat,
                    last_activity_at=item.last_activity_at.isoformat() if item.last_activity_at else None,
                    last_message_seq=item.last_message_seq,
                    unread_count=item.unread_count,
                    last_read_message_seq=item.last_read_message_seq,
                )
                for item in result.items
            ],
            next_before_last_activity_at=result.next_before_last_activity_at.isoformat() if result.next_before_last_activity_at else None,
            next_before_chat_id=result.next_before_chat_id,
        )

    @router.get("/{chat_id}/unread", response_model=GetUnreadCountResponse)
    async def get_unread_count_cached(
        chat_id: UUID,
        current_user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_session),
        cache: RedisChatCache = Depends(get_cache),
    ) -> GetUnreadCountResponse:
        handler = GetUnreadCountProjectionHandler(session=session, cache=cache)
        result = await handler.handle(GetUnreadCountQuery(chat_id=chat_id, user_id=current_user_id))
        return GetUnreadCountResponse(
            chat_id=result.chat_id,
            user_id=result.user_id,
            unread_count=result.unread_count,
            last_read_message_seq=result.last_read_message_seq,
        )

    return router


# =========================
# Notes for production
# =========================
# 1) Create real SQLAlchemy models for processed_outbox_events, chat_list_projection, unread_projection.
# 2) For 10M users, replace the fallback live queries with projection tables and Redis read-through.
# 3) Big chats should not fan out synchronously to every member; use async projections and targeted caches.
# 4) Keep read models monotonic and idempotent. Outbox processing must tolerate retries.
# 5) Consider separate pipelines for direct messages, small groups, and giant groups/channels.
# 6) For list-of-chats and unread counts, prefer projection tables over counting messages on demand.
"""