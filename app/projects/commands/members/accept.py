from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from app.projects.repositories.projects import ProjectRepository
from app.projects.exceptions import NotFoundProjectException

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AcceptInviteCommand(BaseCommand):
    user_jwt_data: UserJWTData
    project_id: int


@dataclass(frozen=True)
class AcceptInviteCommandHandler(BaseCommandHandler[AcceptInviteCommand, None]):
    session: AsyncSession
    project_repository: ProjectRepository
    event_bus: BaseEventBus

    async def handle(self, command: AcceptInviteCommand) -> None:
        user_id = int(command.user_jwt_data.id)
        membership = await self.project_repository.get_membership(command.project_id, user_id)
        if not membership:
            raise NotFoundProjectException(project_id=command.project_id)

        membership.accept_invite()

        await self.session.commit()
        await self.event_bus.publish(membership.pull_events())
        await self.project_repository.invadate_cache()

        logger.info("Invite accepted", extra={"project_id": command.project_id, "user_id": user_id})
