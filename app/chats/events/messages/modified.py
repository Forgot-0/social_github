
from dataclasses import dataclass

from app.chats.keys import ChatKeys
from app.chats.models.message import ModifyMessageEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSEventType
from app.core.events.event import BaseEventHandler
from app.core.websockets.base import BaseConnectionManager


@dataclass(frozen=True)
class ModifiedMessageEventHandler(BaseEventHandler[ModifyMessageEvent, None]):
    connection_manager: BaseConnectionManager
    chat_repository: ChatRepository

    async def __call__(self, event: ModifyMessageEvent) -> None:
        member_ids = await self.chat_repository.get_member_user_ids(event.chat_id)
        playload = {
            "type": WSEventType.MESSAGE_EDITED,
            "chat_id": event.chat_id,
            "payload": {"message_id": event.message_id, "content": event.new_content},
        }
        for uid in member_ids:
            await self.connection_manager.publish(ChatKeys.user_channel(uid), playload)

