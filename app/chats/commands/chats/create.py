from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.services.livekit_service import LiveKitService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.chats.dtos.chats import ChatDetailDTO
from app.chats.models.chat import Chat, ChatType
from app.chats.repositories.chat import ChatRepository


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateChatCommand(BaseCommand):
    name: str | None
    description: str | None
    chat_type: ChatType
    member_ids: list[int]
    is_public: bool
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class CreateChatCommandHandler(BaseCommandHandler[CreateChatCommand, ChatDetailDTO]):
    session: AsyncSession
    chat_repository: ChatRepository
    livekit_sevice: LiveKitService
    event_bus: BaseEventBus

    async def handle(self, command: CreateChatCommand) -> ChatDetailDTO:
        created_by = int(command.user_jwt_data.id)
        chat = Chat.create(
            name=command.name,
            description=command.description,
            created_by=created_by,
            members_ids=command.member_ids,
            chat_type=command.chat_type,
            is_public=command.is_public,
        )
        await self.chat_repository.create(chat)
        await self.session.commit()
        await self.event_bus.publish(chat.pull_events())
        await self.livekit_sevice.create_room(str(chat.id))

        logger.info(
            "Create chat", extra={
                "chat_id": str(chat.id),
                "chat_type": command.chat_type.value,
                "created_by": command.user_jwt_data.id,
            }
        )

        return ChatDetailDTO.model_validate(chat.to_dict())
