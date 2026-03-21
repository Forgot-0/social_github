from dataclasses import dataclass, field
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.models.chat import Chat, ChatType
from app.chats.repositories.chat import ChatRepository
from app.core.commands import BaseCommand, BaseCommandHandler
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

    async def handle(self, command: CreateChatCommand) -> int:
        creator_id = int(command.user_jwt_data.id)
        all_member_ids = list(command.member_ids)

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
