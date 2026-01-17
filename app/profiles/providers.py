from dishka import Provider, Scope, decorate, provide

from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry
from app.profiles.repositories.profiles import ProfileRepository


class ProfileModuleProvider(Provider):
    scope = Scope.REQUEST

    profile_repository = provide(ProfileRepository)

    @decorate
    def register_profile_command_handlers(self, command_registry: CommandRegisty) -> CommandRegisty:
        return command_registry

    @decorate
    def register_profile_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        return event_registry

    @decorate
    def register_profile_query_handlers(self, query_registry: QueryRegistry) -> QueryRegistry:
        return query_registry

