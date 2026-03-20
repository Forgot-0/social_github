from dishka import Provider, Scope, decorate, provide

from app.chats.commands.messages.send_message import SendMessageCommand, SendMessageCommandHandler
from app.chats.commands.reads.mark_read import MarkReadCommand, MarkReadCommandHandler
from app.chats.events.messages.sended import SendedMessageEventHandler
from app.chats.models.chat import SendedMessageEvent
from app.chats.queries.messages.get_list_by_chat import GetMessagesQuery, GetMessagesQueryHandler
from app.chats.repositories.chats import ChatRepository
from app.chats.repositories.messages import MessageRepository
from app.chats.repositories.read_receipts import ReadReceiptRepository
from app.core.events.event import EventRegisty
from app.core.mediators.base import CommandRegisty, QueryRegistry


class ChatModuleProvider(Provider):
    scope = Scope.REQUEST

    chat_repository = provide(ChatRepository)
    message_repository = provide(MessageRepository)
    reads_repository = provide(ReadReceiptRepository)

    mark_read_handler = provide(MarkReadCommandHandler)
    send_message_handler = provide(SendMessageCommandHandler)
    get_messages_handler = provide(GetMessagesQueryHandler)

    @decorate
    def register_chat_commands(self, registry: CommandRegisty) -> CommandRegisty:
        registry.register_command(SendMessageCommand, [SendMessageCommandHandler])
        registry.register_command(MarkReadCommand, [MarkReadCommandHandler])

        return registry

    @decorate
    def register_chat_queries(self, registry: QueryRegistry) -> QueryRegistry:
        registry.register_query(GetMessagesQuery, GetMessagesQueryHandler)
        return registry


    sended_handler = provide(SendedMessageEventHandler)

    @decorate
    def register_profile_event_handlers(self, event_registry: EventRegisty) -> EventRegisty:
        event_registry.subscribe(SendedMessageEvent, [SendedMessageEventHandler])

        return event_registry