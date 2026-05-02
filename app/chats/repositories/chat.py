from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import selectinload

from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.chats.models.permission import ChatRolesEnum
from app.chats.models.read_receipts import ReadReceipt
from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter


@dataclass
class ChatRepository(IRepository[Chat], CacheRepository):
    _LIST_VERSION_KEY = "chats:list"

    async def get_by_id(
        self, chat_id: UUID, with_members: bool = False
    ) -> Chat | None:
        stmt = select(Chat).where(
            Chat.id == chat_id,
            Chat.deleted_at.is_(None),
        )

        if with_members:
            stmt = stmt.options(selectinload(Chat.members))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_member_chat(self, chat_id: UUID, member_id: int, with_role=True) -> ChatMember | None:
        stmt = select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == member_id,
        )
        if with_role:
            stmt = stmt.options(selectinload(ChatMember.role))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def delete_member(self, member: ChatMember) -> None:
        await self.session.delete(member)

    async def iter_member_ids(
        self,
        chat_id: UUID,
        batch_size: int = 2_000,
        role_ids: set[int] | None = None,
    ) -> AsyncIterator[list[int]]:
        last_user_id = -1
        while True:
            conditions = [
                ChatMember.chat_id == chat_id,
                ChatMember.is_banned.is_(False),
                ChatMember.user_id > last_user_id,
            ]
            if role_ids is not None:
                conditions.append(ChatMember.role_id.in_(role_ids))

            stmt = (
                select(ChatMember.user_id)
                .where(*conditions)
                .order_by(ChatMember.user_id.asc())
                .limit(batch_size)
            )
            result = await self.session.execute(stmt)
            user_ids = list(result.scalars().all())
            if not user_ids:
                break
            yield [int(user_id) for user_id in user_ids]
            last_user_id = int(user_ids[-1])

    async def iter_channel_subscriber_ids(
        self,
        chat_id: UUID,
        batch_size: int = 2_000,
    ) -> AsyncIterator[list[int]]:
        async for batch in self.iter_member_ids(
            chat_id=chat_id,
            batch_size=batch_size,
            role_ids=ChatRolesEnum.channel_subscriber_role_ids(),
        ):
            yield batch

    async def iter_channel_staff_ids(
        self,
        chat_id: UUID,
        batch_size: int = 2_000,
    ) -> AsyncIterator[list[int]]:
        async for batch in self.iter_member_ids(
            chat_id=chat_id,
            batch_size=batch_size,
            role_ids=ChatRolesEnum.channel_staff_role_ids(),
        ):
            yield batch


    async def get_chat_members(
        self,
        chat_id: UUID,
        limit: int,
        cursor_user_id: int | None = None,
    ) -> list[ChatMember]:
        conditions = [
            ChatMember.chat_id == chat_id,
            ChatMember.is_banned.is_(False),
        ]
        if cursor_user_id is not None:
            conditions.append(ChatMember.user_id > cursor_user_id)

        stmt = (
            select(ChatMember)
            .where(*conditions)
            .options(selectinload(ChatMember.role))
            .order_by(ChatMember.user_id.asc())
            .limit(limit + 1)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_public_chats(
        self,
        limit: int,
        cursor_last_activity_at: datetime | None = None,
        cursor_chat_id: UUID | None = None,
    ) -> list[Chat]:
        stmt = (
            select(Chat)
            .where(
                Chat.is_public.is_(True),
                Chat.deleted_at.is_(None),
            )
            .order_by(Chat.last_activity_at.desc().nullslast(), Chat.id.desc())
            .limit(limit + 1)
        )
        if cursor_last_activity_at is not None and cursor_chat_id is not None:
            stmt = stmt.where(
                or_(
                    Chat.last_activity_at < cursor_last_activity_at,
                    and_(
                        Chat.last_activity_at == cursor_last_activity_at,
                        Chat.id < cursor_chat_id,
                    ),
                )
            )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, chat: Chat) -> None:
        self.session.add(chat)

    async def get_chats(
        self, user_id: int, limit: int,
        last_activity_at: datetime | None=None, chat_id: UUID | None=None
    ) -> list[tuple[Chat, ChatMember, ReadReceipt | None]]:
        stmt = select(Chat, ChatMember, ReadReceipt).where(
            ChatMember.user_id==user_id,
            ChatMember.is_banned.is_(False),
            Chat.deleted_at.is_(None),
        ).join(
            ChatMember, and_(ChatMember.chat_id == Chat.id, ChatMember.user_id==user_id)
        ).outerjoin(
            ReadReceipt,
            and_(
                ReadReceipt.chat_id == Chat.id,
                ReadReceipt.user_id == user_id,
            ),
        ).order_by(
            Chat.last_activity_at.desc().nullslast(), Chat.id.desc()
        ).limit(limit + 1)

        if last_activity_at is not None and chat_id is not None:
            stmt = stmt.where(
                or_(
                    Chat.last_activity_at < last_activity_at,
                    and_(
                        Chat.last_activity_at == last_activity_at,
                        Chat.id < chat_id,
                    ),
                )
            )

        result = await self.session.execute(stmt)
        return list(*result.all())

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
