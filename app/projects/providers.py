from dishka import Provider, Scope, decorate, provide

from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository


class ProjectModuleProvider(Provider):
    scope = Scope.REQUEST

    project_repository = provide(ProjectRepository)
    project_role_repository = provide(ProjectRoleRepository)

    @decorate
    def register_project_command_handlers(self, command_registry: CommandRegisty) -> CommandRegisty:

        return command_registry

    @decorate
    def register_project_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:

        return event_registry

    @decorate
    def register_project_query_handlers(self, query_registry: QueryRegistry) -> QueryRegistry:

        return query_registry

