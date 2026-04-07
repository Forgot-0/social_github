from dishka import Provider, Scope, decorate, provide, provide_all

from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry
from app.projects.commands.applications.create import (
    CreateApplicationCommand,
    CreateApplicationCommandHandler,
)
from app.projects.commands.applications.decision import (
    DecideApplicationCommand,
    DecideApplicationCommandHandler,
)
from app.projects.commands.members.change_role import ChangeRoleMemberCommand, ChangeRoleMemberCommandHandler
from app.projects.commands.positions.create import (
    CreatePositionCommand,
    CreatePositionCommandHandler,
)
from app.projects.commands.positions.delete import (
    DeletePositionCommand,
    DeletePositionCommandHandler,
)
from app.projects.commands.positions.update import (
    UpdatePositionCommand,
    UpdatePositionCommandHandler,
)
from app.projects.commands.projects.delete import DeleteProjectCommand, DeleteProjectCommandHandler
from app.projects.queries.applications.get_list import (
    GetApplicationsQuery,
    GetApplicationsQueryHandler,
)
from app.projects.queries.positions.get_by_id import (
    GetPositionByIdQuery,
    GetPositionByIdQueryHandler,
)
from app.projects.queries.positions.get_list import (
    GetProjectPositionsQuery,
    GetProjectPositionsQueryHandler,
)
from app.projects.queries.profiles.get_my_invites import GetProfileInvitesQuery, GetProfileInvitesQueryHandler
from app.projects.repositories.applications import ApplicationRepository
from app.projects.repositories.members import MemberProjectRepository
from app.projects.repositories.positions import PositionRepository
from app.projects.repositories.projects import ProjectRepository
from app.projects.repositories.roles import ProjectRoleRepository
from app.projects.commands.projects.create import (
    CreateProjectCommand,
    CreateProjectCommandHandler,
)
from app.projects.commands.projects.update import (
    UpdateProjectCommand,
    UpdateProjectCommandHandler,
)
from app.projects.commands.projects.invite import (
    InviteMemberCommand,
    InviteMemberCommandHandler,
)
from app.projects.queries.projects.get_by_id import (
    GetProjectByIdQuery,
    GetProjectByIdQueryHandler,
)
from app.projects.queries.projects.get_list import (
    GetProjectsQuery,
    GetProjectsQueryHandler,
)
from app.projects.queries.projects.get_my import (
    GetMyProjectsQuery,
    GetMyProjectsQueryHandler,
)
from app.projects.commands.members.accept import (
    AcceptInviteCommand,
    AcceptInviteCommandHandler,
)
from app.projects.commands.members.update_permissions import (
    UpdateMemberPermissionsCommand,
    UpdateMemberPermissionsCommandHandler,
)
from app.projects.commands.roles.create import (
    CreateProjectRoleCommand,
    CreateProjectRoleCommandHandler,
)
from app.projects.commands.roles.update import (
    UpdateProjectRoleCommand,
    UpdateProjectRoleCommandHandler,
)
from app.projects.queries.roles.get_list import (
    GetProjectRolesQuery,
    GetProjectRolesQueryHandler,
)
from app.projects.services.permission_service import ProjectPermissionService


class ProjectModuleProvider(Provider):
    scope = Scope.REQUEST

    # repositories
    project_repository = provide(ProjectRepository)
    project_role_repository = provide(ProjectRoleRepository)
    position_repository = provide(PositionRepository)
    application_repository = provide(ApplicationRepository)
    member_repository = provide(MemberProjectRepository)

    # service
    project_permission_service = provide(
        ProjectPermissionService, scope=Scope.APP
    )

    project_handlers = provide_all(
        CreateProjectCommandHandler,
        DeleteProjectCommandHandler,
        UpdateProjectCommandHandler,
        InviteMemberCommandHandler,
        AcceptInviteCommandHandler,
        UpdateMemberPermissionsCommandHandler,
        ChangeRoleMemberCommandHandler,

        CreatePositionCommandHandler,
        UpdatePositionCommandHandler,
        DeletePositionCommandHandler,

        CreateProjectRoleCommandHandler,
        UpdateProjectRoleCommandHandler,

        CreateApplicationCommandHandler,
        DecideApplicationCommandHandler,

        GetProjectByIdQueryHandler,
        GetProjectsQueryHandler,
        GetMyProjectsQueryHandler,
        GetProjectRolesQueryHandler,
        GetProjectPositionsQueryHandler,
        GetPositionByIdQueryHandler,
        GetApplicationsQueryHandler,
        GetProfileInvitesQueryHandler,
    )

    @decorate
    def register_project_command_handlers(self, command_registry: CommandRegisty) -> CommandRegisty:

        command_registry.register_command(CreateProjectCommand, [CreateProjectCommandHandler])
        command_registry.register_command(DeleteProjectCommand, [DeleteProjectCommandHandler])
        command_registry.register_command(UpdateProjectCommand, [UpdateProjectCommandHandler])
        command_registry.register_command(InviteMemberCommand, [InviteMemberCommandHandler])
        command_registry.register_command(AcceptInviteCommand, [AcceptInviteCommandHandler])
        command_registry.register_command(UpdateMemberPermissionsCommand, [UpdateMemberPermissionsCommandHandler])
        command_registry.register_command(ChangeRoleMemberCommand, [ChangeRoleMemberCommandHandler])

        command_registry.register_command(CreatePositionCommand, [CreatePositionCommandHandler])
        command_registry.register_command(UpdatePositionCommand, [UpdatePositionCommandHandler])
        command_registry.register_command(DeletePositionCommand, [DeletePositionCommandHandler])

        command_registry.register_command(CreateProjectRoleCommand, [CreateProjectRoleCommandHandler])
        command_registry.register_command(UpdateProjectRoleCommand, [UpdateProjectRoleCommandHandler])

        command_registry.register_command(CreateApplicationCommand, [CreateApplicationCommandHandler])
        command_registry.register_command(DecideApplicationCommand, [DecideApplicationCommandHandler])

        return command_registry

    @decorate
    def register_project_query_handlers(self, query_registry: QueryRegistry) -> QueryRegistry:

        query_registry.register_query(GetProjectByIdQuery, GetProjectByIdQueryHandler)
        query_registry.register_query(GetProjectsQuery, GetProjectsQueryHandler)
        query_registry.register_query(GetMyProjectsQuery, GetMyProjectsQueryHandler)
        query_registry.register_query(GetProjectRolesQuery, GetProjectRolesQueryHandler)
        query_registry.register_query(GetProjectPositionsQuery, GetProjectPositionsQueryHandler)

        query_registry.register_query(GetPositionByIdQuery, GetPositionByIdQueryHandler)
        query_registry.register_query(GetApplicationsQuery, GetApplicationsQueryHandler)

        query_registry.register_query(GetProfileInvitesQuery, GetProfileInvitesQueryHandler)
        return query_registry

    @decorate
    def register_project_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        return event_registry
