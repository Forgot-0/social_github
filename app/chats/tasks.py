from dataclasses import dataclass
import logging

from dishka.integrations.taskiq import FromDishka, inject
from taskiq import AsyncBroker

from app.core.services.queues.task import BaseTask

logger = logging.getLogger(__name__)


def register_chat_tasks(broker: AsyncBroker) -> None:
    ...

