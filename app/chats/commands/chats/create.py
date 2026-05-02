from dataclasses import dataclass, field
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.services.livekit_service import LiveKitService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.chats.dtos.chats import ChatDTO
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
    admin_only: bool = False
    slow_mode_seconds: int = 0
    permissions: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class CreateChatCommandHandler(BaseCommandHandler[CreateChatCommand, ChatDTO]):
    session: AsyncSession
    chat_repository: ChatRepository
    livekit_sevice: LiveKitService
    event_bus: BaseEventBus

    async def handle(self, command: CreateChatCommand) -> ChatDTO:
        created_by = int(command.user_jwt_data.id)
        chat = Chat.create(
            name=command.name,
            description=command.description,
            created_by=created_by,
            members_ids=command.member_ids,
            chat_type=command.chat_type,
            is_public=command.is_public,
            admin_only=command.admin_only,
            slow_mode_seconds=command.slow_mode_seconds,
            permissions=command.permissions,
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
                "fanout_strategy": chat.fanout_strategy.value,
            }
        )

        return ChatDTO.model_validate(chat.to_dict())
