from dataclasses import dataclass
import logging

from dishka.integrations.taskiq import FromDishka, inject
from taskiq import AsyncBroker

from app.chats.repositories.read_receipts import ReadReceiptRepository
from app.core.services.queues.task import BaseTask

logger = logging.getLogger(__name__)


def register_chat_tasks(broker: AsyncBroker) -> None:
    broker.register_task(
        FlushReadReceiptsTask.run,
        FlushReadReceiptsTask.get_name(),
        labels={
            "schedule": [{"cron": "*/5 * * * *"}]
        },
    )


@dataclass
class FlushReadReceiptsTask(BaseTask):
    __task_name__ = "chat.flush_read_receipts"

    @staticmethod
    @inject
    async def run(
        read_receipt_repository: FromDishka[ReadReceiptRepository],
    ) -> None:
        count = await read_receipt_repository.flush_dirty_keys()
        if count:
            logger.info(
                "Flushed read receipts", extra={"count": count}
            )

