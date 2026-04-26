from taskiq import AsyncBroker

# from app.chats.tasks.read import FlushReadReceiptsTask
# from app.chats.tasks.success_attachment import AttachmentProccessTask


def register_chat_tasks(broker: AsyncBroker) -> None:
    # broker.register_task(
    #     FlushReadReceiptsTask.run,
    #     FlushReadReceiptsTask.get_name(),
    #     labels={
    #         "schedule": [{"cron": "*/5 * * * *"}]
    #     },
    # )

    # broker.register_task(AttachmentProccessTask.run, AttachmentProccessTask.get_name())
    ...