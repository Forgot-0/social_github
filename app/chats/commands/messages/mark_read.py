from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import NotChatMemberException
from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.chats.schemas.ws import WSEventType
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarkAsReadCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: int
    message_id: int


@dataclass(frozen=True)
class MarkAsReadCommandHandler(BaseCommandHandler[MarkAsReadCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    read_receipt_repository: ReadReceiptRepository
    connection_manager: BaseConnectionManager

    async def handle(self, command: MarkAsReadCommand) -> None:
        user_id = int(command.user_jwt_data.id)

        member = await self.chat_repository.get_member(command.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=command.chat_id, user_id=user_id)

        await self.read_receipt_repository.mark_read(
            user_id=user_id,
            chat_id=command.chat_id,
            message_id=command.message_id,
        )
        await self.session.commit()

        member_ids = await self.chat_repository.get_member_user_ids(command.chat_id)
        event = {
            "type": WSEventType.MESSAGES_READ,
            "chat_id": command.chat_id,
            "payload": {
                "user_id": user_id,
                "last_read_message_id": command.message_id,
            },
        }
        keys = [ChatKeys.user_channel(uid) for uid in member_ids if uid != user_id]
        await self.connection_manager.publish_bulk(keys, event)

        logger.debug(
            "Messages marked as read",
            extra={"chat_id": command.chat_id, "user_id": user_id, "up_to": command.message_id},
        )