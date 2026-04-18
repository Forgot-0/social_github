from taskiq import AsyncBroker

from app.chats.tasks.read import FlushReadReceiptsTask


def register_chat_tasks(broker: AsyncBroker) -> None:
    broker.register_task(
        FlushReadReceiptsTask.run,
        FlushReadReceiptsTask.get_name(),
        labels={
            "schedule": [{"cron": "*/5 * * * * *"}]
        },
    )
