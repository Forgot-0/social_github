from dishka import Provider, Scope, decorate, provide, provide_all
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.chats.commands.attachments.request_upload import RequestAttachmentUploadCommandHandler
from app.chats.commands.attachments.success import SuccessUploadAttachmentsCommandHandler
from app.chats.commands.calls.join import JoinCallCommandHandler
from app.chats.commands.calls.mute import MuteParticipantCommandHandler
from app.chats.commands.chats.add_member import AddMemberCommandHandler
from app.chats.commands.chats.ban_member import BanMemberCommandHandler
from app.chats.commands.chats.change_role import ChangeMemberRoleCommandHandler
from app.chats.commands.chats.create import CreateChatCommandHandler
from app.chats.commands.chats.delete import DeleteChatCommandHandler
from app.chats.commands.chats.join import JoinChatCommandHandler
from app.chats.commands.chats.kick import KickMemberCommandHandler
from app.chats.commands.chats.leave import LeaveChatCommandHandler
from app.chats.commands.chats.update import UpdateChatCommandHandler
from app.chats.commands.messages.delete import DeleteMessageCommandHandler
from app.chats.commands.messages.forward import ForwardMessageCommandHandler
from app.chats.commands.messages.mark_read import MarkAsReadCommandHandler
from app.chats.commands.messages.modify import EditMessageCommandHandler
from app.chats.commands.messages.send import SendMessageCommandHandler
from app.chats.config import chat_config
from app.chats.queries.attachments.get_url import GetAttachmentDownloadUrlQueryHandler
from app.chats.queries.chats.get_detail import GetChatDetailQueryHandler
from app.chats.queries.chats.get_list import GetListChatUserQueryHandler
from app.chats.queries.chats.get_members import GetChatMembersQueryHandler
from app.chats.queries.messages.get_context import GetMessageContextQueryHandler
from app.chats.queries.messages.get_detail import GetMessageDetailQueryHandler
from app.chats.queries.messages.get_list import GetMessagesQueryHandler
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
        ...

    @decorate
    def register_auth_query_handlers(self, query_registry: QueryRegistry) -> QueryRegistry:
        ...

    @decorate
    def register_auth_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        ...
