from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert

from app.chats.keys import ChatKeys
from app.chats.models.read_receipts import ReadReceipt
from app.core.db.repository import CacheRepository, IRepository
from app.core.filters.base import BaseFilter
from app.core.utils import now_utc

_UNREAD_INCR_BATCH_SIZE = 1000


@dataclass
class ReadReceiptRepository(IRepository[ReadReceipt], CacheRepository):

    async def mark_read(
        self,
        user_id: int,
        chat_id: int,
        message_id: int,
    ) -> None:
        current = await self.get_last_read(user_id, chat_id)
        if current is not None and current >= message_id:
            return

        pipe = self.redis.pipeline(transaction=True)
        pipe.set(ChatKeys.last_read(user_id, chat_id), str(message_id))
        pipe.set(ChatKeys.unread_count(user_id, chat_id), "0", ex=timedelta(days=1))
        pipe.zadd(ChatKeys.pending_read_receipts(), {f"{user_id}:{chat_id}:{message_id}": now_utc().timestamp()})
        await pipe.execute()

    async def increment_unread(self, user_id: int, chat_id: int) -> int:
        key = ChatKeys.unread_count(user_id, chat_id)
        return await self.redis.incrby(key)

    async def increment_unread_bulk(self, user_ids: list[int], chat_id: int, without_user: int=0) -> None:
        unique_ids = tuple(dict.fromkeys(user_ids))
        for idx in range(0, len(unique_ids), _UNREAD_INCR_BATCH_SIZE):
            batch = unique_ids[idx:idx + _UNREAD_INCR_BATCH_SIZE]
            pipe = self.redis.pipeline()
            for uid in batch:
                if uid != without_user:
                    pipe.incrby(ChatKeys.unread_count(uid, chat_id))
            await pipe.execute()

    async def get_unread_count(self, user_id: int, chat_id: int) -> int:
        key = ChatKeys.unread_count(user_id, chat_id)
        val = await self.redis.get(key)
        return int(val) if val is not None else 0

    
    async def _upsert_read_receipt(
        self, user_id: int, chat_id: int, message_id: int
    ) -> None:
        stmt = insert(ReadReceipt).values(
            user_id=user_id,
            chat_id=chat_id,
            last_read_message_id=message_id,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_read_receipt",
            set_={"last_read_message_id": message_id},
            where=(ReadReceipt.last_read_message_id < message_id),
        )
        await self.session.execute(stmt)
        await self.session.flush()

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
