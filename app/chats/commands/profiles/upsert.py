import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.repositories.user_profile import ChatUserProfileRepository
from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.utils import now_utc

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpsertProfileProjectionCommand(BaseCommand):
    user_id: int
    username: str
    display_name: str | None = None
    avatars: dict[str, Any] = field(default_factory=dict)



@dataclass(frozen=True)
class UpsertProfileProjectionCommandHandler(
    BaseCommandHandler[UpsertProfileProjectionCommand, None]
):
    session: AsyncSession
    profile_repository: ChatUserProfileRepository

    async def handle(self, command: UpsertProfileProjectionCommand) -> None:
        await self.profile_repository.upsert(
            user_id=command.user_id,
            username=command.username,
            display_name=command.display_name,
            avatars=command.avatars,
            revision=now_utc(),
        )
        await self.session.commit()

        logger.info("Profile projection updated", extra={"user_id": command.user_id})
