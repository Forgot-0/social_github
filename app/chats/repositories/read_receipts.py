from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert

from app.chats.models.read_receipts import ReadReceipt
from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter


@dataclass
class ReadReceiptRepository(IRepository[ReadReceipt], CacheRepository):

    REDIS_TTL = timedelta(days=30)
    DIRTY_SET_KEY = "reads:dirty"

    async def set_cursor(
        self,
        chat_id: int,
        user_id: int,
        message_id: int,
    ) -> None:
        lua = """
        local cur = redis.call('GET', KEYS[1])
        if cur == false or tonumber(ARGV[1]) > tonumber(cur) then
            redis.call('SETEX', KEYS[1], ARGV[2], ARGV[1])
            redis.call('SADD', KEYS[2], KEYS[1])
            return 1
        end
        return 0
        """
        key = f"read:{chat_id}:{user_id}"
        await self.redis.eval(
            lua, 2,
            key, self.DIRTY_SET_KEY,
            message_id, int(self.REDIS_TTL.total_seconds()), # type: ignore
        )

    async def get_cursor(self, chat_id: int, user_id: int) -> int:
        key = f"read:{chat_id}:{user_id}"
        val = await self.redis.get(key)
        return int(val) if val else 0

    async def get_cursors_for_chat(
        self, chat_id: int, user_ids: list[int]
    ) -> dict[int, int]:
        keys = [f"read:{chat_id}:{uid}" for uid in user_ids]
        values = await self.redis.mget(*keys)
        return {
            uid: int(val) if val else 0
            for uid, val in zip(user_ids, values)
        }

    async def flush_dirty_keys(self) -> int:
        dirty_keys: set[bytes] = await self.redis.smembers(self.DIRTY_SET_KEY) # type: ignore
        if not dirty_keys:
            return 0

        await self.redis.delete(self.DIRTY_SET_KEY)

        values = await self.redis.mget(*dirty_keys)
        rows = []
        for key, val in zip(dirty_keys, values):
            if val is None:
                continue

            parts = key.decode().split(":")
            if len(parts) != 3:
                continue
            _, chat_id, user_id = parts

            rows.append({
                "chat_id": int(chat_id),
                "user_id": int(user_id),
                "last_read_message_id": int(val),
            })

        if not rows:
            return 0

        stmt = (
            insert(ReadReceipt)
            .values(rows)
            .on_conflict_do_update(
                constraint="uq_read_receipt",
                set_={"last_read_message_id": insert(ReadReceipt).excluded.last_read_message_id},
                where=insert(ReadReceipt).excluded.last_read_message_id
                      > ReadReceipt.last_read_message_id,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return len(rows)

    async def load_for_chat(self, chat_id: int) -> list[ReadReceipt]:
        result = await self.session.execute(
            select(ReadReceipt).where(ReadReceipt.chat_id == chat_id)
        )
        return list(result.scalars().all())

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt