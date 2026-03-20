import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.models.message import Message
from app.chats.repositories.chats import ChatRepository
from app.chats.repositories.messages import MessageRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.core.message_brokers.base import BaseMessageBroker
from app.core.websockets.base import BaseConnectionManager
from app.core.utils import now_utc

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SendMessageCommand(BaseCommand):
    sender_jwt: UserJWTData
    recipient_id: int
    text: str


@dataclass(frozen=True)
class SendMessageCommandHandler(BaseCommandHandler[SendMessageCommand, int]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    connection_manager: BaseConnectionManager
    event_bus: BaseEventBus

    async def handle(self, command: SendMessageCommand) -> int:
        sender_id = int(command.sender_jwt.id)

        chat = await self.chat_repository.get_or_create(sender_id, command.recipient_id)

        message = Message(
            chat_id=chat.id,
            sender_id=sender_id,
            text=command.text,
        )
        await self.message_repository.create(message)

        chat.send_message(sender_id, command.text, message.id)

        await self.session.commit()
        await self.event_bus.publish(chat.pull_events())

        # payload = {
        #     "event": "new_message",
        #     "chat_id": chat.id,
        #     "id": message.id,
        #     "sender_id": sender_id,
        #     "text": command.text,
        #     "created_at": message.created_at.isoformat(),
        # }
        # await self.connection_manager.publish(
        #     connection_id=f"chat:{chat.id}",
        #     payload=payload,
        # )

        # await self.message_broker.send_data(
        #     key=str(chat.id),
        #     topic="chat.messages",
        #     data=payload,
        # )

        logger.info("Message sent", extra={
            "chat_id": chat.id,
            "message_id": message.id,
            "sender_id": sender_id,
        })
        return message.id
