from dishka import Provider, Scope, decorate, provide, provide_all

from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry
from app.rooms.commands.rooms.add_member import AddMemberRoomCommand, AddMemberRoomCommandHandler
from app.rooms.commands.rooms.ban import BanMemberCommand, BanMemberCommandHandler
from app.rooms.commands.rooms.create import CreateRoomCommand, CreateRoomCommandHandler
from app.rooms.commands.rooms.delete import DeleteRoomCommand, DeleteRoomCommandHandler
from app.rooms.commands.rooms.join import JoinRoomCommand, JoinRoomCommandHandler
from app.rooms.commands.rooms.kick import KickMemberCommand, KickMemberCommandHandler
from app.rooms.commands.rooms.leave import LeaveRoomCommand, LeaveRoomCommandHandler
from app.rooms.commands.rooms.mute import MuteMemberCommand, MuteMemberCommandHandler
from app.rooms.commands.rooms.unban import UnbanMemberCommand, UnbanMemberCommandHandler
from app.rooms.commands.rooms.update import UpdateRoomCommand, UpdateRoomCommandHandler
from app.rooms.config import room_config
from app.rooms.queries.participants.get_list_by_room import GetParticipantsQuery, GetParticipantsQueryHandler
from app.rooms.queries.roles.get_list import GetRolesQuery, GetRolesQueryHandler
from app.rooms.queries.rooms.get import GetRoomQuery, GetRoomQueryHandler
from app.rooms.queries.rooms.get_list import ListRoomsQuery, ListRoomsQueryHandler
from app.rooms.repositories.roles import RoomRoleRepository
from app.rooms.repositories.rooms import RoomRepository
from app.rooms.services.access import RoomAccessService
from app.rooms.services.livekit_service import LiveKitService


class RoomModuleProvider(Provider):
    scope = Scope.REQUEST

    chat_access_service = provide(
        RoomAccessService, scope=Scope.APP
    )

    @provide(scope=Scope.APP)
    def livekit_service(self) -> LiveKitService:
        return LiveKitService(
            url=room_config.LIVEKIT_URL,
            api_key=room_config.LIVEKIT_API_KEY,
            api_secret=room_config.LIVEKIT_API_SECRET,
        )

    repositories = provide_all(
        RoomRoleRepository, RoomRepository
    )

    handlers = provide_all(
        AddMemberRoomCommandHandler,
        BanMemberCommandHandler,
        CreateRoomCommandHandler,
        DeleteRoomCommandHandler,
        JoinRoomCommandHandler,
        KickMemberCommandHandler,
        LeaveRoomCommandHandler,
        MuteMemberCommandHandler,
        UnbanMemberCommandHandler,
        UpdateRoomCommandHandler,

        GetParticipantsQueryHandler,
        GetRolesQueryHandler,
        GetRoomQueryHandler,
        ListRoomsQueryHandler,
    )

    @decorate
    def register_chat_commands(self, registry: CommandRegisty) -> CommandRegisty:
        registry.register_command(CreateRoomCommand, [CreateRoomCommandHandler])
        registry.register_command(DeleteRoomCommand, [DeleteRoomCommandHandler])
        registry.register_command(UpdateRoomCommand, [UpdateRoomCommandHandler])
        registry.register_command(AddMemberRoomCommand, [AddMemberRoomCommandHandler])
        registry.register_command(BanMemberCommand, [BanMemberCommandHandler])
        registry.register_command(JoinRoomCommand, [JoinRoomCommandHandler])
        registry.register_command(KickMemberCommand, [KickMemberCommandHandler])
        registry.register_command(LeaveRoomCommand, [LeaveRoomCommandHandler])
        registry.register_command(MuteMemberCommand, [MuteMemberCommandHandler])
        registry.register_command(UnbanMemberCommand, [UnbanMemberCommandHandler])
        return registry

    @decorate
    def register_chat_queries(self, registry: QueryRegistry) -> QueryRegistry:
        registry.register_query(GetParticipantsQuery, GetParticipantsQueryHandler)
        registry.register_query(GetRolesQuery, GetRolesQueryHandler)
        registry.register_query(GetRoomQuery, GetRoomQueryHandler)
        registry.register_query(ListRoomsQuery, ListRoomsQueryHandler)
        return registry

    @decorate
    def register_chat_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        return event_registry