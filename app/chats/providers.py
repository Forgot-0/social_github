from dishka import Provider, Scope, decorate, provide, provide_all
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.chats.commands.attachments.request_upload import RequestAttachmentUploadCommand, RequestAttachmentUploadCommandHandler
from app.chats.commands.attachments.success import SuccessUploadAttachmentsCommand, SuccessUploadAttachmentsCommandHandler
from app.chats.commands.calls.join import JoinCallCommand, JoinCallCommandHandler
from app.chats.commands.calls.mute import MuteParticipantCommand, MuteParticipantCommandHandler
from app.chats.commands.chats.add_member import AddMemberCommand, AddMemberCommandHandler
from app.chats.commands.chats.ban_member import BanMemberCommand, BanMemberCommandHandler
from app.chats.commands.chats.change_role import ChangeMemberRoleCommand, ChangeMemberRoleCommandHandler
from app.chats.commands.chats.create import CreateChatCommand, CreateChatCommandHandler
from app.chats.commands.chats.delete import DeleteChatCommand, DeleteChatCommandHandler
from app.chats.commands.chats.join import JoinChatCommand, JoinChatCommandHandler
from app.chats.commands.chats.kick import KickMemberCommand, KickMemberCommandHandler
from app.chats.commands.chats.leave import LeaveChatCommand, LeaveChatCommandHandler
from app.chats.commands.chats.update import UpdateChatCommand, UpdateChatCommandHandler
from app.chats.commands.messages.delete import DeleteMessageCommand, DeleteMessageCommandHandler
from app.chats.commands.messages.forward import ForwardMessageCommand, ForwardMessageCommandHandler
from app.chats.commands.messages.mark_read import MarkAsReadCommand, MarkAsReadCommandHandler
from app.chats.commands.messages.modify import EditMessageCommand, EditMessageCommandHandler
from app.chats.commands.messages.send import SendMessageCommand, SendMessageCommandHandler
from app.chats.config import chat_config
from app.chats.events.published import PublishChatEventHandler
from app.chats.models.chat import (
    AddedChatMemberEvent,
    BannedChatMemberEvent,
    CreatedChatEvent,
    DeletedChatEvent,
    KickedChatMemberEvent,
    LeftChatMemberEvent,
    UpdatedChatEvent,
)
from app.chats.models.message import (
    DeletedMessageEvent,
    ModifiedMessageEvent,
    ReadedMessageEvent,
    SendedMessageEvent,
)
from app.chats.queries.attachments.get_url import GetAttachmentDownloadUrlQuery, GetAttachmentDownloadUrlQueryHandler
from app.chats.queries.chats.get_detail import GetChatDetailQuery, GetChatDetailQueryHandler
from app.chats.queries.chats.get_list import GetListChatUserQuery, GetListChatUserQueryHandler
from app.chats.queries.chats.get_members import GetChatMembersQuery, GetChatMembersQueryHandler
from app.chats.queries.messages.get_context import GetMessageContextQuery, GetMessageContextQueryHandler
from app.chats.queries.messages.get_detail import GetMessageDetailQuery, GetMessageDetailQueryHandler
from app.chats.queries.messages.get_list import GetMessagesQuery, GetMessagesQueryHandler
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.delivery_router import ChatDeliveryRouter
from app.chats.services.livekit_service import LiveKitService
from app.chats.services.presence import PresenceService
from app.chats.services.slow_mode import SlowModeService
from app.chats.services.ws import ChatConnectionManager
from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry
from app.core.websockets.base import BaseConnectionManager


class ChatModuleProvider(Provider):
    @provide(scope=Scope.APP)
    def connection_manager(self, redis: Redis) -> BaseConnectionManager:
        return ChatConnectionManager(redis=redis)

    @provide(scope=Scope.APP)
    def delivery_router(
        self, redis: Redis, marker: async_sessionmaker[AsyncSession]
    ) -> ChatDeliveryRouter:
        return ChatDeliveryRouter(redis=redis, session_factory=marker)

    @provide(scope=Scope.REQUEST)
    def livekit_service(self) -> LiveKitService:
        return LiveKitService(
            url=chat_config.LIVEKIT_URL,
            api_key=chat_config.LIVEKIT_API_KEY,
            api_secret=chat_config.LIVEKIT_API_SECRET,
        )

    commands = provide_all(
        RequestAttachmentUploadCommandHandler,
        SuccessUploadAttachmentsCommandHandler,
        JoinCallCommandHandler,
        MuteParticipantCommandHandler,
        AddMemberCommandHandler,
        BanMemberCommandHandler,
        ChangeMemberRoleCommandHandler,
        CreateChatCommandHandler,
        DeleteChatCommandHandler,
        JoinChatCommandHandler,
        KickMemberCommandHandler,
        LeaveChatCommandHandler,
        UpdateChatCommandHandler,
        DeleteMessageCommandHandler,
        ForwardMessageCommandHandler,
        MarkAsReadCommandHandler,
        EditMessageCommandHandler,
        SendMessageCommandHandler,
        scope=Scope.REQUEST,
    )

    queries = provide_all(
        GetAttachmentDownloadUrlQueryHandler,
        GetChatDetailQueryHandler,
        GetListChatUserQueryHandler,
        GetChatMembersQueryHandler,
        GetMessageContextQueryHandler,
        GetMessageDetailQueryHandler,
        GetMessagesQueryHandler,
        scope=Scope.REQUEST,
    )

    repositories_and_services = provide_all(
        ChatRepository,
        MessageRepository,
        AttachmentRepository,
        ReadReceiptRepository,
        ChatAccessService,
        PresenceService,
        SlowModeService,
        scope=Scope.REQUEST,
    )

    @decorate
    def register_auth_command_handlers(self, command_registry: CommandRegisty) -> CommandRegisty:
        command_registry.register_command(RequestAttachmentUploadCommand, [RequestAttachmentUploadCommandHandler])
        command_registry.register_command(SuccessUploadAttachmentsCommand, [SuccessUploadAttachmentsCommandHandler])
        command_registry.register_command(JoinCallCommand, [JoinCallCommandHandler])
        command_registry.register_command(MuteParticipantCommand, [MuteParticipantCommandHandler])
        command_registry.register_command(AddMemberCommand, [AddMemberCommandHandler])
        command_registry.register_command(BanMemberCommand, [BanMemberCommandHandler])
        command_registry.register_command(ChangeMemberRoleCommand, [ChangeMemberRoleCommandHandler])
        command_registry.register_command(CreateChatCommand, [CreateChatCommandHandler])
        command_registry.register_command(DeleteChatCommand, [DeleteChatCommandHandler])
        command_registry.register_command(JoinChatCommand, [JoinChatCommandHandler])
        command_registry.register_command(KickMemberCommand, [KickMemberCommandHandler])
        command_registry.register_command(LeaveChatCommand, [LeaveChatCommandHandler])
        command_registry.register_command(UpdateChatCommand, [UpdateChatCommandHandler])
        command_registry.register_command(DeleteMessageCommand, [DeleteMessageCommandHandler])
        command_registry.register_command(ForwardMessageCommand, [ForwardMessageCommandHandler])
        command_registry.register_command(MarkAsReadCommand, [MarkAsReadCommandHandler])
        command_registry.register_command(EditMessageCommand, [EditMessageCommandHandler])
        command_registry.register_command(SendMessageCommand, [SendMessageCommandHandler])
        return command_registry

    @decorate
    def register_auth_query_handlers(self, query_registry: QueryRegistry) -> QueryRegistry:
        query_registry.register_query(GetAttachmentDownloadUrlQuery, GetAttachmentDownloadUrlQueryHandler)
        query_registry.register_query(GetChatDetailQuery, GetChatDetailQueryHandler)
        query_registry.register_query(GetListChatUserQuery, GetListChatUserQueryHandler)
        query_registry.register_query(GetChatMembersQuery, GetChatMembersQueryHandler)
        query_registry.register_query(GetMessageContextQuery, GetMessageContextQueryHandler)
        query_registry.register_query(GetMessageDetailQuery, GetMessageDetailQueryHandler)
        query_registry.register_query(GetMessagesQuery, GetMessagesQueryHandler)
        return query_registry

    @decorate
    def register_auth_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        event_registry.subscribe(CreatedChatEvent, [PublishChatEventHandler])
        event_registry.subscribe(UpdatedChatEvent, [PublishChatEventHandler])
        event_registry.subscribe(DeletedChatEvent, [PublishChatEventHandler])
        event_registry.subscribe(AddedChatMemberEvent, [PublishChatEventHandler])
        event_registry.subscribe(KickedChatMemberEvent, [PublishChatEventHandler])
        event_registry.subscribe(BannedChatMemberEvent, [PublishChatEventHandler])
        event_registry.subscribe(LeftChatMemberEvent, [PublishChatEventHandler])
        event_registry.subscribe(SendedMessageEvent, [PublishChatEventHandler])
        event_registry.subscribe(ModifiedMessageEvent, [PublishChatEventHandler])
        event_registry.subscribe(DeletedMessageEvent, [PublishChatEventHandler])
        event_registry.subscribe(ReadedMessageEvent, [PublishChatEventHandler])
        return event_registry
