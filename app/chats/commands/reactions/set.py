import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import (
    InvalidReactionError,
    NotChatMemberError,
    NotFoundChatError,
    NotFoundMessageError,
    TooManyReactionsError,
)
from app.chats.config import chat_config
from app.chats.models.reaction import ReactionUpdatedEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.repositories.reaction import MessageReactionRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SetReactionCommand(BaseCommand):
    chat_id: UUID
    message_id: UUID
    emoji: str
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class SetReactionCommandHandler(BaseCommandHandler[SetReactionCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    reaction_repository: MessageReactionRepository
    event_bus: BaseEventBus

    async def handle(self, command: SetReactionCommand) -> None:
        if (
            not command.emoji or
            len(command.emoji) > chat_config.MAX_REACRTION_LENGTH or
            "\x00" in command.emoji or command.emoji.isspace()
        ):
                raise InvalidReactionError(emoji=command.emoji[:64])

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

        distinct_emojis = await self.reaction_repository.count_distinct_emojis(
            command.message_id
        )
        current_count = await self.reaction_repository.get_counter(
            command.message_id, command.emoji
        )
        if current_count == 0 and distinct_emojis >= chat_config.MAX_REACTIONS_PER_MESSAGE:
            raise TooManyReactionsError

        old_emoji, changed = await self.reaction_repository.set_reaction(
            chat_id=command.chat_id,
            message_id=command.message_id,
            user_id=user_id,
            emoji=command.emoji,
        )

        if not changed:
            await self.session.rollback()
            return

        events: list[ReactionUpdatedEvent] = []
        if old_emoji is not None:
            old_count = await self.reaction_repository.get_counter(
                command.message_id, old_emoji
            )
            events.append(
                ReactionUpdatedEvent(
                    message_id=str(command.message_id),
                    chat_id=str(command.chat_id),
                    emoji=old_emoji,
                    count=old_count,
                    changed_by=user_id,
                )
            )

        new_count = await self.reaction_repository.get_counter(
            command.message_id, command.emoji
        )
        events.append(
            ReactionUpdatedEvent(
                message_id=str(command.message_id),
                chat_id=str(command.chat_id),
                emoji=command.emoji,
                count=new_count,
                changed_by=user_id,
            )
        )

        await self.event_bus.publish(events)
        await self.session.commit()

        logger.info(
            "Reaction set",
            extra={
                "chat_id": str(command.chat_id),
                "message_id": str(command.message_id),
                "user_id": user_id,
                "emoji": command.emoji,
                "replaced": old_emoji,
            },
        )
