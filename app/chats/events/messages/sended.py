from dataclasses import dataclass

from app.chats.models.chat import SendedMessageEvent
from app.core.events.event import BaseEventHandler
from app.core.message_brokers.base import BaseMessageBroker
from app.core.websockets.base import BaseConnectionManager


@dataclass(frozen=True)
class SendedMessageEventHandler(BaseEventHandler[SendedMessageEvent, None]):
    connection_manager: BaseConnectionManager
    message_broker: BaseMessageBroker

    async def __call__(self, event: SendedMessageEvent) -> None:
        payload = {
            "event": "new_message",
            "chat_id": event.chat_id,
            "id": event.message_id,
            "sender_id": event.sender_id,
            "text": event.text,
            "created_at": event.created_at.isoformat(),
        }
        await self.connection_manager.publish(
            key=f"chat:{event.chat_id}",
            payload=payload,
        )

        await self.message_broker.send_event(
            key=str(event.chat_id),
            topic="chat.messages",
            event=event
        )

