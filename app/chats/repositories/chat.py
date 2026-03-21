from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.chats.keys import ChatKeys
from app.chats.models.chat import Chat, ChatType
from app.chats.models.chat_members import ChatMember, MemberRole
from app.core.db.repository import CacheRepository, IRepository, PageResult
from app.core.filters.base import BaseFilter


@dataclass
class ChatRepository(IRepository[Chat], CacheRepository):
    redis: Redis
    _LIST_VERSION_KEY: str = "chats:list"

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

    async def get_user_chats(
        self, user_id: int, page: int = 1, page_size: int = 20
    ) -> PageResult[Chat]:
        stmt = (
            select(Chat)
            .join(ChatMember, ChatMember.chat_id == Chat.id)
            .where(
                ChatMember.user_id == user_id,
                ChatMember.is_banned.is_(False),
                Chat.deleted_at.is_(None),
            )
            .options(selectinload(Chat.members))
            .order_by(Chat.last_activity_at.desc().nullslast())
            .distinct()
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(stmt.offset(offset).limit(page_size))
        items = list(result.scalars().all())

        return PageResult(items=items, total=total, page=page, page_size=page_size)

    async def get_direct_chat(
        self, user_id_1: int, user_id_2: int
    ) -> Chat | None:
        sub = (
            select(ChatMember.chat_id)
            .where(ChatMember.user_id.in_([user_id_1, user_id_2]))
            .group_by(ChatMember.chat_id)
            .having(func.count(ChatMember.user_id) == 2)
            .subquery()
        )

        stmt = select(Chat).where(
            Chat.id.in_(select(sub)),
            Chat.type == ChatType.DIRECT,
            Chat.deleted_at.is_(None),
        )

        result = await self.session.execute(stmt)
        return result.scalar()

    async def create(self, chat: Chat) -> Chat:
        self.session.add(chat)
        await self.session.flush()
        return chat

    async def get_member(
        self, chat_id: int, user_id: int
    ) -> ChatMember | None:
        result = await self.session.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id,
            )
        )
        return result.scalar()

    async def get_members(self, chat_id: int) -> list[ChatMember]:
        result = await self.session.execute(
            select(ChatMember).where(ChatMember.chat_id == chat_id)
        )
        return list(result.scalars().all())

    async def add_member(
        self,
        chat_id: int,
        user_id: int,
        role: MemberRole = MemberRole.MEMBER,
    ) -> None:
        member = ChatMember(
            chat_id=chat_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(member)

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

    async def get_member_user_ids(self, chat_id: int) -> list[int]:
        result = await self.session.execute(
            select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
        )
        return list(result.scalars().all())

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt