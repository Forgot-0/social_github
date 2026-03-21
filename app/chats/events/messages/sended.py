from dataclasses import dataclass
from datetime import datetime

from app.chats.exceptions import NotChatMemberException
from app.chats.keys import ChatKeys
from app.chats.models.message import MessageType
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.chats.schemas.ws import WSEventType, WSNewMessagePayload
from app.core.events.event import BaseEvent, BaseEventHandler
from app.core.websockets.base import BaseConnectionManager


@dataclass(frozen=True)
class SendedMessageEvent(BaseEvent):
    chat_id: int
    sender_id: int
    message_id: int
    content: str | None
    send_at: datetime
    reply_to_id: int | None = None
    is_edited: bool = False
    message_type: MessageType = MessageType.TEXT



@dataclass(frozen=True)
class SendedMessageEventHandler(BaseEventHandler[SendedMessageEvent, None]):
    read_receipt_repository: ReadReceiptRepository
    connection_manager: BaseConnectionManager
    chat_repository: ChatRepository

    async def __call__(self, event: SendedMessageEvent) -> None:
        payload = WSNewMessagePayload(
            id=event.message_id,
            chat_id=event.chat_id,
            author_id=event.sender_id,
            content=event.content,
            created_at=event.created_at,
            is_edited=event.is_edited,
            reply_to_id=event.reply_to_id,
        )

        data = {
            "type": WSEventType.NEW_MESSAGE,
            "chat_id": event.chat_id,
            "payload": payload.model_dump(),
        }

        member_ids = await self.chat_repository.get_member_user_ids(event.chat_id)

        for uid in member_ids:
            if uid != event.sender_id:
                await self.read_receipt_repository.increment_unread(uid, event.chat_id)

            channel_key = ChatKeys.user_channel(uid)
            await self.connection_manager.publish(channel_key, data)

