from dataclasses import dataclass
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException
from app.chats.models.message import ReadedMessageEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarkAsReadCommand(BaseCommand):
    chat_id: UUID
    message_seq: int

    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class MarkAsReadCommandHandler(BaseCommandHandler[MarkAsReadCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    access_service: ChatAccessService
    read_receipt_repository: ReadReceiptRepository
    event_bus: BaseEventBus

    async def handle(self, command: MarkAsReadCommand) -> None:
        user_id = int(command.user_jwt_data.id)

        member = await self.chat_repository.get_member_chat(command.chat_id, user_id)
        if not member:
            raise NotChatMemberException(chat_id=str(command.chat_id), user_id=user_id)

        if not await self.access_service.has_permissions(
            user_jwt_data=command.user_jwt_data,
            member=member,
            must_permissions={"message:read"}
        ): raise AccessDeniedChatException(chat_id=str(command.chat_id), requester_id=user_id)

        await self.read_receipt_repository.mark_read(
            user_id=user_id,
            chat_id=command.chat_id,
            message_seq=command.message_seq,
        )
        await self.session.commit()
        await self.event_bus.publish([ReadedMessageEvent(
            chat_id=str(command.chat_id),
            seq=command.message_seq,
            reader_id=user_id
        )])

        logger.info(
            "Messages marked as read",
            extra={"chat_id": command.chat_id, "user_id": user_id, "up_to": command.message_seq},
        )
