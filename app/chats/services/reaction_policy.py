from dataclasses import dataclass

from app.chats.exceptions import (
    AccessDeniedChatError,
    InvalidReactionError,
    ReactionNotAllowedError,
    ReactionsDisabledError,
)
from app.chats.models.chat import Chat, ChatReactionsMode
from app.chats.models.chat_members import ChatMember
from app.chats.reactions.catalog import DEFAULT_REACTION_SET


@dataclass(slots=True)
class ReactionPolicy:
    """Validates whether a member may react to a message in a given chat with a
    given emoji. Mirrors Telegram: muted members cannot react, a chat can allow
    every default reaction, a curated subset, or disable reactions entirely."""

    def ensure_can_react(self, chat: Chat, member: ChatMember) -> None:
        if member.is_muted:
            raise AccessDeniedChatError(
                chat_id=str(chat.id), requester_id=member.user_id
            )
        if chat.reactions_mode == ChatReactionsMode.NONE:
            raise ReactionsDisabledError(chat_id=str(chat.id))

    def validate_emoji(self, chat: Chat, emoji: str) -> None:
        if emoji not in DEFAULT_REACTION_SET:
            raise InvalidReactionError(emoji=emoji[:64])

        if chat.reactions_mode == ChatReactionsMode.NONE:
            raise ReactionsDisabledError(chat_id=str(chat.id))

        if (
            chat.reactions_mode == ChatReactionsMode.SOME
            and emoji not in set(chat.allowed_reactions or ())
        ):
            raise ReactionNotAllowedError(
                emoji=emoji, allowed=list(chat.allowed_reactions or [])
            )

    def validate(self, chat: Chat, member: ChatMember, emoji: str) -> None:
        self.ensure_can_react(chat, member)
        self.validate_emoji(chat, emoji)
