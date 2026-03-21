from dishka import Provider, Scope, decorate, provide

from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry


class ChatModuleProvider(Provider):
    scope = Scope.REQUEST

    @decorate
    def register_chat_commands(self, registry: CommandRegisty) -> CommandRegisty:

        return registry

    @decorate
    def register_chat_queries(self, registry: QueryRegistry) -> QueryRegistry:
        return registry



    @decorate
    def register_profile_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        return event_registry