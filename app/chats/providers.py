from dishka import Provider, Scope, decorate, provide, provide_all
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.add_member import AddMemberCommand, AddMemberCommandHandler
from app.chats.commands.chats.ban_member import BanMemberCommand, BanMemberCommandHandler
from app.chats.commands.chats.change_role import ChangeMemberRoleCommand, ChangeMemberRoleCommandHandler
from app.chats.commands.chats.create import CreateChatCommand, CreateChatCommandHandler

from app.chats.commands.chats.kick_member import KickMemberCommand, KickMemberCommandHandler
from app.chats.commands.chats.leave import LeaveChatCommand, LeaveChatCommandHandler
from app.chats.commands.chats.update import UpdateChatCommand, UpdateChatCommandHandler
from app.chats.commands.messages.delete import DeleteMessageCommand, DeleteMessageCommandHandler
from app.chats.commands.messages.mark_read import MarkAsReadCommand, MarkAsReadCommandHandler
from app.chats.commands.messages.modify import (
    EditMessageCommand, EditMessageCommandHandler,
)
from app.chats.commands.messages.send import SendMessageCommand, SendMessageCommandHandler
from app.chats.events.members.kicked import KickedChatMemberEventHandler
from app.chats.events.members.leaved import LeavedChatMemberEventHandler
from app.chats.events.messages.deleted import DeletedMessageEventHandler
from app.chats.events.messages.modified import ModifiedMessageEventHandler
from app.chats.events.messages.sended import SendedMessageEvent, SendedMessageEventHandler
from app.chats.models.chat import KickedChatMemberEvent, LeavedChatMemberEvent
from app.chats.models.message import DeletedMessageEvent, ModifiedMessageEvent
from app.chats.queries.chats.get_by_id import GetChatByIdQuery, GetChatByIdQueryHandler
from app.chats.queries.chats.get_my_list import GetChatsQuery, GetChatsQueryHandler
from app.chats.queries.chats.presence import (
    GetChatPresenceQuery, GetChatPresenceQueryHandler,
    GetMessageDeliveryQuery, GetMessageDeliveryQueryHandler,
)
from app.chats.queries.messages.get_list import GetMessagesQuery, GetMessagesQueryHandler
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.delivery import DeliveryTrackingService
from app.chats.services.presence import PresenceService
from app.chats.services.ws_client_events import ChatWebSocketClientService
from app.core.websockets.base import BaseConnectionManager
from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry


class ChatModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def chat_repository(self, session: AsyncSession, redis: Redis) -> ChatRepository:
        return ChatRepository(session=session, redis=redis)

    @provide
    def message_repository(self, session: AsyncSession) -> MessageRepository:
        return MessageRepository(session=session)

    @provide
    def read_receipt_service(self, redis: Redis, session: AsyncSession) -> ReadReceiptRepository:
        return ReadReceiptRepository(redis=redis, session=session)


    @provide(scope=Scope.APP)
    def presence_service(self, redis: Redis) -> PresenceService:
        return PresenceService(redis=redis)

    @provide(scope=Scope.APP)
    def delivery_tracking_service(self, redis: Redis) -> DeliveryTrackingService:
        return DeliveryTrackingService(redis=redis)

    caht_access_service = provide(
        ChatAccessService, scope=Scope.APP
    )


    @provide
    def chat_websocket_client_service(
        self,
        chat_repository: ChatRepository,
        connection_manager: BaseConnectionManager,
        delivery_tracking_service: DeliveryTrackingService,
    ) -> ChatWebSocketClientService:
        return ChatWebSocketClientService(
            chat_repository=chat_repository,
            connection_manager=connection_manager,
            delivery_service=delivery_tracking_service,
        )


    chat_handlers = provide_all(
        CreateChatCommandHandler,
        AddMemberCommandHandler,
        KickMemberCommandHandler,
        LeaveChatCommandHandler,
        BanMemberCommandHandler,
        ChangeMemberRoleCommandHandler,
        UpdateChatCommandHandler,
        SendMessageCommandHandler,
        DeleteMessageCommandHandler,
        EditMessageCommandHandler,
        MarkAsReadCommandHandler,

        GetChatsQueryHandler,
        GetChatByIdQueryHandler,
        GetMessagesQueryHandler,
        GetChatPresenceQueryHandler,
        GetMessageDeliveryQueryHandler,

        KickedChatMemberEventHandler,
        LeavedChatMemberEventHandler,
        DeletedMessageEventHandler,
        ModifiedMessageEventHandler,
        SendedMessageEventHandler,
    )

    @decorate
    def register_chat_commands(self, registry: CommandRegisty) -> CommandRegisty:
        registry.register_command(CreateChatCommand, [CreateChatCommandHandler])
        registry.register_command(AddMemberCommand, [AddMemberCommandHandler])
        registry.register_command(KickMemberCommand, [KickMemberCommandHandler])
        registry.register_command(LeaveChatCommand, [LeaveChatCommandHandler])
        registry.register_command(BanMemberCommand, [BanMemberCommandHandler])
        registry.register_command(ChangeMemberRoleCommand, [ChangeMemberRoleCommandHandler])
        registry.register_command(UpdateChatCommand, [UpdateChatCommandHandler])
        registry.register_command(SendMessageCommand, [SendMessageCommandHandler])
        registry.register_command(DeleteMessageCommand, [DeleteMessageCommandHandler])
        registry.register_command(EditMessageCommand, [EditMessageCommandHandler])
        registry.register_command(MarkAsReadCommand, [MarkAsReadCommandHandler])
        return registry

    @decorate
    def register_chat_queries(self, registry: QueryRegistry) -> QueryRegistry:
        registry.register_query(GetChatsQuery, GetChatsQueryHandler)
        registry.register_query(GetChatByIdQuery, GetChatByIdQueryHandler)
        registry.register_query(GetMessagesQuery, GetMessagesQueryHandler)
        registry.register_query(GetChatPresenceQuery, GetChatPresenceQueryHandler)
        registry.register_query(GetMessageDeliveryQuery, GetMessageDeliveryQueryHandler)
        return registry

    @decorate
    def register_chat_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        event_registry.subscribe(KickedChatMemberEvent, [KickedChatMemberEventHandler])
        event_registry.subscribe(LeavedChatMemberEvent, [LeavedChatMemberEventHandler])
        event_registry.subscribe(DeletedMessageEvent, [DeletedMessageEventHandler])
        event_registry.subscribe(ModifiedMessageEvent, [ModifiedMessageEventHandler])
        event_registry.subscribe(SendedMessageEvent, [SendedMessageEventHandler])
        return event_registry
