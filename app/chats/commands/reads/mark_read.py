import logging
from dataclasses import dataclass

from app.chats.repositories.read_receipts import ReadReceiptRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarkReadCommand(BaseCommand):
    user_jwt: UserJWTData
    chat_id: int
    message_id: int


@dataclass(frozen=True)
class MarkReadCommandHandler(BaseCommandHandler[MarkReadCommand, None]):
    read_receipt_repository: ReadReceiptRepository
    connection_manager: BaseConnectionManager

    async def handle(self, command: MarkReadCommand) -> None:
        user_id = int(command.user_jwt.id)

        await self.read_receipt_repository.set_cursor(
            chat_id=command.chat_id,
            user_id=user_id,
            message_id=command.message_id,
        )

        await self.connection_manager.publish(
            key=f"chat:{command.chat_id}",
            payload={
                "event": "message_read",
                "chat_id": command.chat_id,
                "reader_id": user_id,
                "last_read_message_id": command.message_id,
            },
        )

        logger.info("Mark read", extra={
            "chat_id": command.chat_id,
            "user_id": user_id,
            "message_id": command.message_id,
        })
