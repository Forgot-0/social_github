from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReactionSummaryDTO(BaseModel):
    emoji: str
    count: int
    reacted_by_me: bool = False


class ReactionUserDTO(BaseModel):
    user_id: int
    emoji: str

    model_config = ConfigDict(from_attributes=True)


class MessageReactionsDTO(BaseModel):
    message_id: UUID
    summaries: list[ReactionSummaryDTO] = Field(default_factory=list)

    emoji: str | None = None
    users: list[ReactionUserDTO] = Field(default_factory=list)
    has_next: bool = False
    next_user_id: int | None = None
