from dataclasses import dataclass
import logging

from redis.asyncio import Redis
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from dishka.integrations.taskiq import FromDishka, inject
from taskiq import AsyncBroker

from app.chats.keys import ChatKeys
from app.chats.models.read_receipts import ReadReceipt
from app.core.services.queues.task import BaseTask

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000



def register_chat_tasks(broker: AsyncBroker) -> None:
    broker.register_task(
        FlushReadReceiptsTask.run,
        FlushReadReceiptsTask.get_name(),
        labels={
            "schedule": [{"cron": "*/5 * * * * *"}]
        },
    )


@dataclass
class FlushReadReceiptsTask(BaseTask):
    __task_name__ = "chat.flush_read_receipts"

    @staticmethod
    @inject
    async def run(
        session: FromDishka[AsyncSession],
        redis: FromDishka[Redis],
    ) -> None:
        pending_keys = await redis.zrange(ChatKeys.pending_read_receipts(), 0, BATCH_SIZE - 1)
        if not pending_keys:
            return

        records = []
        keys_to_remove = []

        for key_bytes in pending_keys:
            key = key_bytes.decode()
            try:
                user_id_str, chat_id_str, message_id_str = key.split(":")
                user_id = int(user_id_str)
                chat_id = int(chat_id_str)
                message_id = int(message_id_str)
            except ValueError:
                await redis.zrem(ChatKeys.pending_read_receipts(), key)
                continue

            records.append({
                "user_id": user_id,
                "chat_id": chat_id,
                "last_read_message_id": message_id,
            })
            keys_to_remove.append(key)

        if records:
            stmt = insert(ReadReceipt).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "chat_id"],
                set_={
                    "last_read_message_id": stmt.excluded.last_read_message_id,
                }
            )
            await session.execute(stmt)
            await session.commit()

        if keys_to_remove:
            await redis.zrem(ChatKeys.pending_read_receipts(), *keys_to_remove)

        logger.info(
            "Flushed read receipts", extra={"count": len(keys_to_remove)}
        )
