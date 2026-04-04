from dataclasses import dataclass
from datetime import datetime

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
    sender_id: int | None
    message_id: int
    content: str | None
    send_at: datetime
    reply_to_id: int | None = None
    is_edited: bool = False
    message_type: MessageType = MessageType.TEXT
    attachment_count: int = 0
    forwarded_from_chat_id: int | None = None
    forwarded_from_message_id: int | None = None


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
            created_at=event.send_at,
            is_edited=event.is_edited,
            reply_to_id=event.reply_to_id,
            attachment_count=event.attachment_count,
            forwarded_from_chat_id=event.forwarded_from_chat_id,
            forwarded_from_message_id=event.forwarded_from_message_id,
        )

        data = {
            "type": WSEventType.NEW_MESSAGE,
            "chat_id": event.chat_id,
            "payload": payload.model_dump(),
        }

        member_ids = await self.chat_repository.get_member_user_ids(event.chat_id)
        await self.read_receipt_repository.increment_unread_bulk(
            user_ids=member_ids,
            chat_id=event.chat_id,
            without_user=event.sender_id or 0,
        )

        await self.connection_manager.publish(
            ChatKeys.chat_channel(event.chat_id),
            data,
        )
