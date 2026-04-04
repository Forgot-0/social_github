from dataclasses import dataclass

from app.chats.config import chat_config
from app.chats.models.chat import AddedChatMemberEvent
from app.core.events.event import BaseEventHandler
from app.core.message_brokers.base import BaseMessageBroker


@dataclass(frozen=True)
class AddedChatMemberEventHandler(BaseEventHandler[AddedChatMemberEvent, None]):
    message_broker: BaseMessageBroker

    async def __call__(self, event: AddedChatMemberEvent) -> None:
        await self.message_broker.send_event(
            key=str(event.chat_id),
            topic=chat_config.CHAT_TOPIC,
            event=event
        )
