from dishka import Provider, Scope, decorate, provide

from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.commands.projects.create import CreateProjectCommand, CreateProjectCommandHandler
from app.projects.commands.projects.update import UpdateProjectCommand, UpdateProjectCommandHandler
from app.projects.commands.projects.invite import InviteMemberCommand, InviteMemberCommandHandler
from app.projects.queries.projects.get_by_id import GetProjectByIdQuery, GetProjectByIdQueryHandler
from app.projects.queries.projects.get_list import GetProjectsQuery, GetProjectsQueryHandler
from app.projects.commands.members.accept import AcceptInviteCommand, AcceptInviteCommandHandler
from app.projects.commands.members.update_permissions import (
    UpdateMemberPermissionsCommand,
    UpdateMemberPermissionsCommandHandler
)
from app.projects.commands.roles.create import CreateProjectRoleCommand, CreateProjectRoleCommandHandler
from app.projects.commands.roles.update import UpdateProjectRoleCommand, UpdateProjectRoleCommandHandler
from app.projects.queries.roles.get_list import GetProjectRolesQuery, GetProjectRolesQueryHandler
from app.projects.services.permission_service import ProjectPermissionService


class ProjectModuleProvider(Provider):
    scope = Scope.REQUEST

    project_repository = provide(ProjectRepository)
    project_role_repository = provide(ProjectRoleRepository)

    project_permission_servise = provide(ProjectPermissionService, scope=Scope.APP)

    create_project_handler = provide(CreateProjectCommandHandler)
    update_project_handler = provide(UpdateProjectCommandHandler)
    invite_member_handler = provide(InviteMemberCommandHandler)

    accept_invite_handler = provide(AcceptInviteCommandHandler)
    update_member_permissions_handler = provide(UpdateMemberPermissionsCommandHandler)

    create_role_handler = provide(CreateProjectRoleCommandHandler)
    update_role_handler = provide(UpdateProjectRoleCommandHandler)
    get_roles_handler = provide(GetProjectRolesQueryHandler)

    get_by_id_project_handler = provide(GetProjectByIdQueryHandler)
    get_projects_handler = provide(GetProjectsQueryHandler)

    @decorate
    def register_project_command_handlers(self, command_registry: CommandRegisty) -> CommandRegisty:

        command_registry.register_command(
            CreateProjectCommand,
            [CreateProjectCommandHandler]
        )
        command_registry.register_command(
            UpdateProjectCommand,
            [UpdateProjectCommandHandler]
        )
        command_registry.register_command(
            InviteMemberCommand,
            [InviteMemberCommandHandler]
        )
        command_registry.register_command(
            AcceptInviteCommand,
            [AcceptInviteCommandHandler]
        )
        command_registry.register_command(
            UpdateMemberPermissionsCommand,
            [UpdateMemberPermissionsCommandHandler]
        )

        command_registry.register_command(
            CreateProjectRoleCommand,
            [CreateProjectRoleCommandHandler]
        )
        command_registry.register_command(
            UpdateProjectRoleCommand,
            [UpdateProjectRoleCommandHandler]
        )

        return command_registry

    @decorate
    def register_project_query_handlers(self, query_registry: QueryRegistry) -> QueryRegistry:

        query_registry.register_query(
            GetProjectByIdQuery,
            GetProjectByIdQueryHandler
        )
        query_registry.register_query(
            GetProjectsQuery,
            GetProjectsQueryHandler
        )
        query_registry.register_query(
            GetProjectRolesQuery,
            GetProjectRolesQueryHandler
        )

        return query_registry

    @decorate
    def register_project_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:

        return event_registry
