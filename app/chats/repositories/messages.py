from dataclasses import dataclass
from datetime import timedelta

import orjson
from redis.asyncio import Redis
from sqlalchemy import Select, select, update

from app.chats.models.message import Message
from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter


@dataclass
class MessageRepository(IRepository[Message], CacheRepository):
    _LIST_VERSION_KEY = "message:list"

    async def create(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_page(
        self,
        chat_id: int,
        limit: int = 30,
        before_id: int | None = None,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id, Message.is_deleted.is_(False))
        )
        if before_id is not None:
            stmt = stmt.where(Message.id < before_id)

        stmt = stmt.order_by(Message.id.desc()).limit(limit + 1)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(self, chat_id: int, user_id: int, up_to_message_id: int) -> None:
        key = f"read:{chat_id}:{user_id}"
        await self.redis.set(key, up_to_message_id, ex=timedelta(days=30))

    async def get_read_cursor(self, chat_id: int, user_id: int) -> int:
        key = f"read:{chat_id}:{user_id}"
        val = await self.redis.get(key)
        return int(val) if val else 0

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt