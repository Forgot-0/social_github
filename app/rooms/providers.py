
from dishka import Provider, Scope, decorate, provide, provide_all

from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry
from app.rooms.commands.rooms.add_member import AddMemberRoomCommand, AddMemberRoomCommandHandler
from app.rooms.commands.rooms.create import CreateRoomCommand, CreateRoomCommandHandler
from app.rooms.commands.rooms.delete import DeleteRoomCommand, DeleteRoomCommandHandler
from app.rooms.commands.rooms.update import UpdateRoomCommand, UpdateRoomCommandHandler
from app.rooms.config import room_config
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
    def livekit_service(self, ) -> LiveKitService:
        return LiveKitService(
            url=room_config.LIVEKIT_URL,
            api_key=room_config.LIVEKIT_API_KEY,
            api_secret=room_config.LIVEKIT_API_SECRET
        )

    repositories = provide_all(
        RoomRoleRepository, RoomRepository
    )

    handlers = provide_all(
        AddMemberRoomCommandHandler,
        CreateRoomCommandHandler,
        DeleteRoomCommandHandler,
        UpdateRoomCommandHandler
    )

    @decorate
    def register_chat_commands(self, registry: CommandRegisty) -> CommandRegisty:
        registry.register_command(CreateRoomCommand, [CreateRoomCommandHandler])
        registry.register_command(DeleteRoomCommand, [DeleteRoomCommandHandler])
        registry.register_command(UpdateRoomCommand, [UpdateRoomCommandHandler])

        registry.register_command(AddMemberRoomCommand, [AddMemberRoomCommandHandler])
        return registry

    @decorate
    def register_chat_queries(self, registry: QueryRegistry) -> QueryRegistry:
        return registry

    @decorate
    def register_chat_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        return event_registry
