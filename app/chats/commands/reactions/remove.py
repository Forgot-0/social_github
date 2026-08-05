import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import NotChatMemberError, NotFoundChatError, NotFoundMessageError
from app.chats.models.reaction import ReactionUpdatedEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.repositories.reaction import MessageReactionRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class RemoveReactionCommand(BaseCommand):
    chat_id: UUID
    message_id: UUID
    emoji: str
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class RemoveReactionCommandHandler(BaseCommandHandler[RemoveReactionCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    reaction_repository: MessageReactionRepository
    event_bus: BaseEventBus

    async def handle(self, command: RemoveReactionCommand) -> None:
        user_id = int(command.user_jwt_data.id)

        chat = await self.chat_repository.get_by_id(command.chat_id)
        if chat is None:
            raise NotFoundChatError(chat_id=str(command.chat_id))

        member = await self.chat_repository.get_member_chat(
            command.chat_id, user_id, with_role=False
        )
        if member is None or member.is_banned:
            raise NotChatMemberError(chat_id=str(command.chat_id), user_id=user_id)

        message = await self.message_repository.get_by_id(command.message_id)
        if message is None or message.chat_id != command.chat_id:
            raise NotFoundMessageError(message_id=str(command.message_id))

        removed = await self.reaction_repository.remove_reaction(
            message_id=command.message_id,
            user_id=user_id,
            emoji=command.emoji,
        )

        if not removed:
            await self.session.rollback()
            return

        count = await self.reaction_repository.get_counter(
            command.message_id, command.emoji
        )
        await self.event_bus.publish([
            ReactionUpdatedEvent(
                message_id=str(command.message_id),
                chat_id=str(command.chat_id),
                emoji=command.emoji,
                count=count,
                changed_by=user_id,
            )
        ])
        await self.session.commit()

        logger.info(
            "Reaction removed",
            extra={
                "chat_id": str(command.chat_id),
                "message_id": str(command.message_id),
                "user_id": user_id,
                "emoji": command.emoji,
            },
        )
