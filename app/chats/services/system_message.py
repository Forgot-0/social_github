import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.models.message import Message, MessageType
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.core.events.service import BaseEventBus

logger = logging.getLogger(__name__)


@dataclass
class SystemMessageService:
    session: AsyncSession
    message_repository: MessageRepository
    chat_repository: ChatRepository
    event_bus: BaseEventBus

    async def send(self, chat_id: int, content: str) -> None:
        from app.chats.events.messages.sended import SendedMessageEvent

        msg = Message.create(
            sender_id=None,
            chat_id=chat_id,
            content=content,
            message_type=MessageType.SYSTEM,
        )
        msg = await self.message_repository.create(msg)

        chat = await self.chat_repository.get_by_id(chat_id)
        if chat:
            try:
                chat.update_last_activity(message_id=msg.id, message_date=msg.created_at)
            except Exception:
                pass

        await self.session.commit()

        await self.event_bus.publish([
            SendedMessageEvent(
                chat_id=chat_id,
                sender_id=None,
                message_id=msg.id,
                content=content,
                send_at=msg.created_at,
                message_type=MessageType.SYSTEM,
            )
        ])

        logger.debug(
            "System message sent",
            extra={"chat_id": chat_id, "content": content},
        )
