
from dataclasses import dataclass

from app.chats.keys import ChatKeys
from app.chats.models.message import DeletedMessageEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSEventType
from app.core.events.event import BaseEventHandler
from app.core.websockets.base import BaseConnectionManager


@dataclass(frozen=True)
class DeletedMessageEventHandler(BaseEventHandler[DeletedMessageEvent, None]):
    connection_manager: BaseConnectionManager
    chat_repository: ChatRepository

    async def __call__(self, event: DeletedMessageEvent) -> None:
        member_ids = await self.chat_repository.get_member_user_ids(event.chat_id)

        payload = {
            "type": WSEventType.MESSAGE_DELETED,
            "chat_id": event.chat_id,
            "payload": {"message_id": event.message_id},
        }
        keys = [ChatKeys.user_channel(uid) for uid in member_ids]
        await self.connection_manager.publish_bulk(keys, payload)
