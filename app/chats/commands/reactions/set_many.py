import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.reactions import build_reaction_event
from app.chats.config import chat_config
from app.chats.exceptions import (
    NotChatMemberError,
    NotFoundMessageError,
    TooManyReactionsError,
)
from app.chats.metrics import CHAT_REACTIONS_APPLIED, CHAT_REACTIONS_REJECTED
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.repositories.reaction import MessageReactionRepository
from app.chats.services.reaction_policy import ReactionPolicy
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SetReactionsCommand(BaseCommand):
    """Replace the caller's whole reaction set for a message (set-semantics,
    like Telegram ``messages.sendReaction``). An empty list clears all."""

    chat_id: UUID
    message_id: UUID
    emojis: tuple[str, ...]
    user_jwt_data: UserJWTData


@dataclass(frozen=True)
class SetReactionsCommandHandler(BaseCommandHandler[SetReactionsCommand, None]):
    session: AsyncSession
    chat_repository: ChatRepository
    message_repository: MessageRepository
    reaction_repository: MessageReactionRepository
    reaction_policy: ReactionPolicy
    event_bus: BaseEventBus

    async def handle(self, command: SetReactionsCommand) -> None:
        user_id = int(command.user_jwt_data.id)
        target = list(dict.fromkeys(command.emojis))

        chat, member = await self.chat_repository.get_chat_and_member(
            chat_id=command.chat_id, member_id=user_id
        )
        if member.is_banned:
            CHAT_REACTIONS_REJECTED.labels(reason="not_member").inc()
            raise NotChatMemberError(chat_id=str(command.chat_id), user_id=user_id)

        message = await self.message_repository.get_by_id(command.message_id)
        if message is None or message.chat_id != command.chat_id:
            CHAT_REACTIONS_REJECTED.labels(reason="message_not_found").inc()
            raise NotFoundMessageError(message_id=str(command.message_id))

        if target:
            self.reaction_policy.ensure_can_react(chat, member)
            for emoji in target:
                try:
                    self.reaction_policy.validate_emoji(chat, emoji)
                except Exception:
                    CHAT_REACTIONS_REJECTED.labels(reason="policy").inc()
                    raise

            if len(target) > chat_config.MAX_REACTIONS_PER_USER_PER_MESSAGE:
                CHAT_REACTIONS_REJECTED.labels(reason="per_user_limit").inc()
                raise TooManyReactionsError(
                    limit=chat_config.MAX_REACTIONS_PER_USER_PER_MESSAGE, scope="user"
                )

            new_emojis = set(target) - set(
                await self.reaction_repository.list_user_emojis(
                    command.message_id, user_id
                )
            )
            if new_emojis:
                distinct = await self.reaction_repository.count_distinct_emojis(
                    command.message_id
                )
                existing_groups = {
                    g.emoji for g in await self.reaction_repository.get_current_groups(
                        command.message_id
                    )
                }
                added_distinct = len(new_emojis - existing_groups)
                if distinct + added_distinct > chat_config.MAX_DISTINCT_REACTIONS_PER_MESSAGE:
                    CHAT_REACTIONS_REJECTED.labels(reason="per_message_limit").inc()
                    raise TooManyReactionsError(
                        limit=chat_config.MAX_DISTINCT_REACTIONS_PER_MESSAGE,
                        scope="message",
                    )

        changed = await self.reaction_repository.set_reactions(
            chat_id=command.chat_id,
            message_id=command.message_id,
            user_id=user_id,
            emojis=target,
        )
        if not changed:
            return

        event = await build_reaction_event(
            self.reaction_repository,
            chat_id=command.chat_id,
            message_id=command.message_id,
            actor_id=user_id,
            action="replace",
        )
        await self.event_bus.publish([event])
        await self.session.commit()

        CHAT_REACTIONS_APPLIED.labels(action="replace").inc()
        logger.info(
            "Reactions replaced",
            extra={
                "chat_id": str(command.chat_id),
                "message_id": str(command.message_id),
                "user_id": user_id,
                "emojis": target,
            },
        )
