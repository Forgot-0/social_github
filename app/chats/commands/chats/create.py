import logging
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.keys import ChatKeys
from app.chats.models.chat import Chat, ChatType, CreatedChatEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.services.livekit_service import LiveKitService
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)



@dataclass(frozen=True)
class CreateChatCommand(BaseCommand):
    user_jwt_data: UserJWTData
    chat_type: ChatType
    member_ids: set[int] = field(default_factory=set)
    name: str | None = None
    description: str | None = None
    is_public: bool = False


@dataclass(frozen=True)
class CreateChatCommandHandler(BaseCommandHandler[CreateChatCommand, int]):
    session: AsyncSession
    chat_repository: ChatRepository
    livekit_service: LiveKitService
    event_bus: BaseEventBus

    async def handle(self, command: CreateChatCommand) -> int:
        creator_id = int(command.user_jwt_data.id)

        all_member_ids = list(command.member_ids)
        if creator_id in all_member_ids:
            all_member_ids.remove(creator_id)

        chat = Chat.create(
            created_by=creator_id,
            members_ids=all_member_ids,
            chat_type=command.chat_type,
            name=command.name,
            description=command.description,
            is_public=command.is_public
        )
        await self.chat_repository.create(chat)
        await self.session.commit()
        await self.livekit_service.create_room(slug=ChatKeys.chat_call_slug(chat.id))

        await self.event_bus.publish(
            [CreatedChatEvent(
                chat_id=chat.id,
                created_by=creator_id,
                member_ids=all_member_ids,
                name=chat.name
            )]
        )

        logger.info(
            "Chat created",
            extra={
                "chat_id": chat.id,
                "creator": creator_id,
                "members": len(all_member_ids),
                "chat_type": command.chat_type
            },
        )

        return chat.id
