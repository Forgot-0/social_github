from dataclasses import dataclass
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.dtos.chats import ChatDTO
from app.chats.exceptions import AccessDeniedChatException, NotFoundChatException
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class UpdateChatCommand(BaseCommand):
    chat_id: UUID
    name: str | None
    description: str | None
    is_public: bool

    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class UpdateChatCommandHandler(BaseCommandHandler[UpdateChatCommand, ChatDTO]):
    sessions: AsyncSession
    chat_repository: ChatRepository
    access_service: ChatAccessService
    event_bus: BaseEventBus

    async def handle(self, command: UpdateChatCommand) -> ChatDTO:
        chat = await self.chat_repository.get_by_id(chat_id=command.chat_id)
        if chat is None:
            raise NotFoundChatException(chat_id=str(command.chat_id))

        user_id = int(command.user_jwt_data.id)

        member = await self.chat_repository.get_member_chat(
            chat_id=command.chat_id, member_id=user_id
        )

        if not self.access_service.has_permissions(
            user_jwt_data=command.user_jwt_data,
            member=member,
            must_permissions={"chat:update"}
        ): raise AccessDeniedChatException(
            chat_id=str(command.chat_id), requester_id=user_id
        )

        chat.update(
            updated_by=user_id,
            name=command.name,
            description=command.description,
            is_public=command.is_public
        )

        await self.sessions.commit()
        await self.event_bus.publish(chat.pull_events())

        return ChatDTO.model_validate(chat.to_dict())
