from dataclasses import dataclass
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.core.utils import now_utc
from app.projects.repositories.projects import ProjectRepository
from app.projects.models.member import MembershipStatus
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

    async def handle(self, command: AcceptInviteCommand) -> None:
        user_id = int(command.user_jwt_data.id)
        membership = await self.project_repository.get_membership(command.project_id, user_id)
        if not membership:
            raise NotFoundProjectException(project_id=command.project_id)

        if membership.status not in (MembershipStatus.invited, MembershipStatus.pending):
            raise 

        membership.status = MembershipStatus.active
        membership.joined_at = now_utc()
        await self.session.commit()

        logger.info("Invite accepted", extra={"project_id": command.project_id, "user_id": user_id})
