import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException, NotFoundChatException
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeleteChatCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_id: UUID


@dataclass(frozen=True)
class DeleteChatCommandHandler(BaseCommandHandler[DeleteChatCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    access_service: ChatAccessService
    event_bus: BaseEventBus

    async def handle(self, command: DeleteChatCommand) -> None:
        requester_id = int(command.user_jwt_data.id)
        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=str(command.chat_id))

        member = await self.chat_repository.get_member_chat(command.chat_id, requester_id)
        if member is None:
            raise NotChatMemberException(chat_id=str(command.chat_id), user_id=requester_id)

        if not await self.access_service.has_permissions(
            user_jwt_data=command.user_jwt_data,
            member=member,
            must_permissions={"chat:delete"},
        ):
            raise AccessDeniedChatException(chat_id=str(command.chat_id), requester_id=requester_id)

        chat.delete(deleted_by=requester_id)
        await self.session.commit()
        await self.event_bus.publish(chat.pull_events())
        logger.info("Chat deleted", extra={"chat_id": command.chat_id, "deleted_by": requester_id})
