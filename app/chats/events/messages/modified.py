
from dataclasses import dataclass

from app.chats.keys import ChatKeys
from app.chats.models.message import ModifiedMessageEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSEventType, WSModifyMessagePayload
from app.core.events.event import BaseEventHandler
from app.core.websockets.base import BaseConnectionManager


@dataclass(frozen=True)
class ModifiedMessageEventHandler(BaseEventHandler[ModifiedMessageEvent, None]):
    connection_manager: BaseConnectionManager
    chat_repository: ChatRepository

    async def __call__(self, event: ModifiedMessageEvent) -> None:
        payload = WSModifyMessagePayload(
            id=event.message_id,
            chat_id=event.chat_id,
            author_id=event.modified_by,
            content=event.new_content
        )

        data = {
            "type": WSEventType.MESSAGE_EDITED,
            "chat_id": event.chat_id,
            "payload": payload.model_dump(),
        }
        await self.connection_manager.publish(
            ChatKeys.chat_channel(event.chat_id),
            data,
        )


