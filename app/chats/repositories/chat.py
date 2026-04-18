from dataclasses import dataclass
from datetime import datetime

import orjson
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.chats.keys import ChatKeys
from app.chats.models.chat import Chat
from app.chats.models.chat_members import ChatMember
from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter


@dataclass
class ChatRepository(IRepository[Chat], CacheRepository):
    _LIST_VERSION_KEY = "chats:list"

    async def get_by_id(
        self, chat_id: int, with_members: bool = False
    ) -> Chat | None:
        stmt = select(Chat).where(
            Chat.id == chat_id,
            Chat.deleted_at.is_(None),
        )

        if with_members:
            stmt = stmt.options(selectinload(Chat.members))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_user_chat_ids(self, user_id: int) -> list[int]:
        rows = await self.session.execute(
            select(ChatMember.chat_id)
            .join(Chat, Chat.id == ChatMember.chat_id)
            .where(
                ChatMember.user_id == user_id,
                ChatMember.is_banned.is_(False),
                Chat.deleted_at.is_(None),
            )
        )
        return list(rows.scalars().all())

    async def get_user_chats_cursor(
        self,
        user_id: int,
        limit: int = 20,
        cursor_activity_at: datetime | None = None,
        cursor_chat_id: int | None = None,
    ) -> list[Chat]:
        stmt = (
            select(Chat)
            .join(ChatMember, ChatMember.chat_id == Chat.id)
            .options(
                selectinload(Chat.members).selectinload(ChatMember.role),
            )
            .where(
                ChatMember.user_id == user_id,
                ChatMember.is_banned.is_(False),
                Chat.deleted_at.is_(None),
            )
            .order_by(Chat.last_activity_at.desc().nullslast(), Chat.id.desc())
            .limit(limit + 1)
        )

        if cursor_activity_at is not None and cursor_chat_id is not None:
            stmt = stmt.where(
                or_(
                    Chat.last_activity_at < cursor_activity_at,
                    and_(
                        Chat.last_activity_at == cursor_activity_at,
                        Chat.id < cursor_chat_id,
                    ),
                )
            )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, chat: Chat) -> Chat:
        self.session.add(chat)
        await self.session.flush()
        return chat

    async def get_member(
        self, chat_id: int, user_id: int, with_role: bool=False
    ) -> ChatMember | None:
        stmt = select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user_id,
        )
        if with_role:
            stmt = stmt.options(selectinload(ChatMember.role))

        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_members(self, chat_id: int, limit: int = 1000) -> list[ChatMember]:
        if limit > 10000:
            limit = 10000

        result = await self.session.execute(
            select(ChatMember)
            .where(ChatMember.chat_id == chat_id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_member(
        self,
        chat_id: int,
        user_id: int,
        role_id: int,
    ) -> None:
        member = ChatMember(
            chat_id=chat_id,
            user_id=user_id,
            role_id=role_id,
        )
        self.session.add(member)
        await self.invalidate_cache(ChatKeys.chat_member_count(chat_id))
        await self.invalidate_cache(ChatKeys.chat_members_ids(chat_id))

    async def get_member_count(self, chat_id: int) -> int:
        key = ChatKeys.chat_member_count(chat_id)
        cached = await self.redis.get(key)
        if cached:
            return int(cached)

        result = await self.session.execute(
            select(func.count())
            .select_from(ChatMember)
            .where(ChatMember.chat_id == chat_id)
        )
        count = result.scalar_one()
        await self.redis.setex(key, 300, str(count))
        return count

    async def get_member_counts_bulk(self, chat_ids: list[int]) -> dict[int, int]:
        keys = [ChatKeys.chat_member_count(cid) for cid in chat_ids]
        cached = await self.redis.mget(*keys)

        result: dict[int, int] = {}
        missing: list[int] = []

        for cid, val in zip(chat_ids, cached, strict=False):
            if val is not None:
                result[cid] = int(val)
            else:
                missing.append(cid)

        if missing:
            rows = await self.session.execute(
                select(ChatMember.chat_id, func.count().label("cnt"))
                .where(ChatMember.chat_id.in_(missing))
                .group_by(ChatMember.chat_id)
            )
            pipe = self.redis.pipeline()
            for row in rows:
                result[row.chat_id] = row.cnt
                pipe.setex(ChatKeys.chat_member_count(row.chat_id), 300, str(row.cnt))
            await pipe.execute()

        return result

    async def get_member_user_ids(self, chat_id: int ) -> list[int]:
        key = ChatKeys.chat_members_ids(chat_id)
        cached = await self.redis.get(key)
        if cached:
            return orjson.loads(cached)
        ids = await self._get_member_user_ids(chat_id)
        await self.redis.setex(key, 30, orjson.dumps(ids))
        return ids

    async def _get_member_user_ids(self, chat_id: int, without_member: int | None=None) -> list[int]:
        stmt = select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)

        if without_member is not None:
            stmt = stmt.where(ChatMember.user_id != without_member)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
