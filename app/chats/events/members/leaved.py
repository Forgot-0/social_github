from dataclasses import dataclass

from app.chats.config import chat_config
from app.chats.keys import ChatKeys
from app.chats.models.chat import LeftChatMemberEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSEventType
from app.core.events.event import BaseEventHandler
from app.core.message_brokers.base import BaseMessageBroker
from app.core.websockets.base import BaseConnectionManager


@dataclass(frozen=True)
class LeftChatMemberEventHandler(BaseEventHandler[LeftChatMemberEvent, None]):
    connection_manager: BaseConnectionManager
    chat_repository: ChatRepository
    message_broker: BaseMessageBroker

    async def __call__(self, event: LeftChatMemberEvent) -> None:
        member_ids = await self.chat_repository.get_member_user_ids(event.chat_id)
        await self.connection_manager.unbind_key_connections(
            source_key=ChatKeys.user_channel(event.user_id),
            target_key=ChatKeys.chat_channel(event.chat_id),
        )

        payload = {
            "type": WSEventType.MEMBER_LEFT,
            "chat_id": event.chat_id,
            "payload": {"user_id": event.user_id},
        }
        keys = [ChatKeys.user_channel(uid) for uid in member_ids if uid != event.user_id]
        await self.connection_manager.publish_bulk(keys, payload)
        await self.message_broker.send_event(
            key=str(event.chat_id),
            topic=chat_config.CHAT_TOPIC,
            event=event
        )
