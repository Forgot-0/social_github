from collections.abc import Sequence
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.chats.models.reaction import MessageReaction, MessageReactionCounter


class ReactionSummaryDTO(BaseModel):
    emoji: str
    count: int
    reacted_by_me: bool = False


def build_reaction_summaries(
    counters: Sequence["MessageReactionCounter"],
    user_reactions: Sequence["MessageReaction"],
) -> dict[UUID, list[ReactionSummaryDTO]]:
    my_emojis: dict[UUID, set[str]] = {}
    for reaction in user_reactions:
        my_emojis.setdefault(reaction.message_id, set()).add(reaction.emoji)

    summaries: dict[UUID, list[ReactionSummaryDTO]] = {}
    for counter in counters:
        if counter.count <= 0:
            continue
        summaries.setdefault(counter.message_id, []).append(
            ReactionSummaryDTO(
                emoji=counter.emoji,
                count=counter.count,
                reacted_by_me=counter.emoji in my_emojis.get(counter.message_id, set()),
            )
        )
    return summaries


class ReactionUserDTO(BaseModel):
    user_id: int
    emoji: str

    model_config = ConfigDict(from_attributes=True)


class MessageReactionsDTO(BaseModel):
    message_id: str
    summaries: list[ReactionSummaryDTO] = Field(default_factory=list)

    emoji: str | None = None
    users: list[ReactionUserDTO] = Field(default_factory=list)
    has_next: bool = False
    next_user_id: int | None = None
