from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands import BaseCommand, BaseCommandHandler
from app.core.services.auth.dto import UserJWTData
from app.notifications.exceptions import NotFoundNotificationException, NotificationAccessDeniedException
from app.notifications.repositories.notifications import NotificationRepository


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class MarkNotificationAsReadCommand(BaseCommand):
    user_jwt_data: UserJWTData

    notification_id: int
    is_read: bool = True



@dataclass(frozen=True)
class MarkNotificationAsReadCommandHandler(BaseCommandHandler[MarkNotificationAsReadCommand, None]):
    session: AsyncSession
    notification_repository: NotificationRepository

    async def handle(self, command: MarkNotificationAsReadCommand) -> None:
        notification = await self.notification_repository.get_by_id(command.notification_id)
        if notification is None:
            raise NotFoundNotificationException(notification_id=command.notification_id)

        if notification.user_id != int(command.user_jwt_data.id):
            raise NotificationAccessDeniedException(notification_id=command.notification_id)

        notification.is_read = command.is_read
        await self.notification_repository.invalidate_cache()
        await self.session.commit()
        logger.info(
            "Mark notification as read",
            extra={"user_id": command.user_jwt_data.id, "notification_id": command.notification_id},
        )
