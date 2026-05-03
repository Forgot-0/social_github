from dataclasses import dataclass
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException, NotFoundMessageException
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeleteMessageCommand(BaseCommand):
    chat_id: UUID
    message_id: UUID

    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class DeleteMessageCommandHandler(BaseCommandHandler[DeleteMessageCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    chat_access_service: ChatAccessService
    event_bus: BaseEventBus

    async def handle(self, command: DeleteMessageCommand) -> None:
        user_id = int(command.user_jwt_data.id)

        message = await self.message_repository.get_by_id(command.message_id)
        if message is None or message.chat_id != command.chat_id:
            raise NotFoundMessageException(message_id=str(command.message_id))

        member = await self.chat_repository.get_member_chat(command.chat_id, user_id)
        if member is None:
            raise NotChatMemberException(chat_id=str(command.chat_id), user_id=user_id)

        if (
            message.author_id != user_id and
            not await self.chat_access_service.has_permissions(
                user_jwt_data=command.user_jwt_data,
                member=member,
                must_permissions={"message:delete"}
            )
        ): raise AccessDeniedChatException(chat_id=str(command.chat_id), requester_id=user_id)

        message.delete(deleted_by=user_id)
        await self.session.commit()
        await self.event_bus.publish(message.pull_events())

        logger.info(
            "Message deleted",
            extra={"chat_id": command.chat_id, "message_id": command.message_id, "by": user_id},
        )

