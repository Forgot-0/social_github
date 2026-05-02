from dataclasses import dataclass

from app.chats.config import chat_config
from app.core.events.event import BaseEvent, BaseEventHandler
from app.core.message_brokers.base import BaseMessageBroker


@dataclass(frozen=True)
class PublishChatEventHandler(BaseEventHandler[BaseEvent, None]):
    message_broker: BaseMessageBroker

    async def __call__(self, event: BaseEvent) -> None:
        await self.message_broker.send_event(
            key=event.get_partition_key(),
            topic=chat_config.CHAT_TOPIC,
            event=event
        )
