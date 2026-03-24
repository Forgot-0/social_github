from dataclasses import dataclass

from app.chats.keys import ChatKeys
from app.chats.models.chat import KickedChatMemberEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.schemas.ws import WSEventType
from app.core.events.event import BaseEventHandler
from app.core.websockets.base import BaseConnectionManager


@dataclass(frozen=True)
class KickedChatMemberEventHandler(BaseEventHandler[KickedChatMemberEvent, None]):
    connection_manager: BaseConnectionManager
    chat_repository: ChatRepository

    async def __call__(self, event: KickedChatMemberEvent) -> None:
        member_ids = await self.chat_repository.get_member_user_ids(event.chat_id)
        await self.connection_manager.unbind_key_connections(
            source_key=ChatKeys.user_channel(event.target_user_id),
            target_key=ChatKeys.chat_channel(event.chat_id),
        )

        payload = {
            "type": WSEventType.MEMBER_KICK,
            "chat_id": event.chat_id,
            "payload": {"user_id": event.target_user_id, "kicked_by": event.requester_id},
        }
        keys = [ChatKeys.user_channel(uid) for uid in member_ids]
        await self.connection_manager.publish_bulk(keys, payload)
