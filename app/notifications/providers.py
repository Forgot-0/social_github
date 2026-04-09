from dishka import Provider, Scope, decorate, provide, provide_all

from app.core.mediators.base import CommandRegisty, QueryRegistry
from app.notifications.commands.notifications.mark_all_read import (
    MarkAllNotificationsAsReadCommand,
    MarkAllNotificationsAsReadCommandHandler,
)
from app.notifications.commands.notifications.mark_read import (
    MarkNotificationAsReadCommand,
    MarkNotificationAsReadCommandHandler,
)
from app.notifications.queries.notifications.get_list import GetNotificationsQuery, GetNotificationsQueryHandler
from app.notifications.queries.notifications.get_unread_count import (
    GetUnreadNotificationsCountQuery,
    GetUnreadNotificationsCountQueryHandler,
)
from app.notifications.repositories.notifications import NotificationRepository


class NotificationModuleProvider(Provider):
    scope = Scope.REQUEST

    notification_repository = provide(NotificationRepository)

    handlers = provide_all(
        MarkNotificationAsReadCommandHandler,
        MarkAllNotificationsAsReadCommandHandler,
        GetNotificationsQueryHandler,
        GetUnreadNotificationsCountQueryHandler,
    )

    @decorate
    def register_notification_commands(self, command_registry: CommandRegisty) -> CommandRegisty:
        command_registry.register_command(MarkNotificationAsReadCommand, [MarkNotificationAsReadCommandHandler])
        command_registry.register_command(
            MarkAllNotificationsAsReadCommand,
            [MarkAllNotificationsAsReadCommandHandler],
        )
        return command_registry

    @decorate
    def register_notification_queries(self, query_registry: QueryRegistry) -> QueryRegistry:
        query_registry.register_query(GetNotificationsQuery, GetNotificationsQueryHandler)
        query_registry.register_query(GetUnreadNotificationsCountQuery, GetUnreadNotificationsCountQueryHandler)
        return query_registry
