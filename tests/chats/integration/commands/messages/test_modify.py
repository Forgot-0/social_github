import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.messages.modify import EditMessageCommand, EditMessageCommandHandler
from app.chats.exceptions import AccessDeniedChatException, MessageTooLongException, NotFoundMessageException
from app.chats.models.chat import Chat
from app.chats.models.message import Message, ModifiedMessageEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.core.services.auth.dto import UserJWTData
from tests.conftest import MockEventBus


@pytest.mark.integration
@pytest.mark.chats
class TestEditMessageCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        message_repository: MessageRepository,
        mock_event_bus: MockEventBus,
    ) -> EditMessageCommandHandler:
        return EditMessageCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            message_repository=message_repository,
            event_bus=mock_event_bus,
        )

    @pytest.mark.asyncio
    async def test_author_can_edit_own_message(
        self,
        handler: EditMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        message_repository: MessageRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = EditMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
            new_content="Updated content",
        )

        await handler.handle(command)

        msg = await message_repository.get_by_id(persisted_message.id)
        assert msg is not None
        assert msg.content == "Updated content"
        assert msg.is_edited is True

    @pytest.mark.asyncio
    async def test_edit_publishes_modified_event(
        self,
        handler: EditMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        owner_jwt: UserJWTData,
        mock_event_bus: MockEventBus,
    ) -> None:
        command = EditMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
            new_content="Modified",
        )

        await handler.handle(command)

        assert len(mock_event_bus.published_events) == 1
        event = mock_event_bus.published_events[0]
        assert isinstance(event, ModifiedMessageEvent)
        assert event.new_content == "Modified"

    @pytest.mark.asyncio
    async def test_non_author_cannot_edit(
        self,
        handler: EditMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        member_jwt: UserJWTData,
    ) -> None:
        command = EditMessageCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
            new_content="Hijacked content",
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_edit_nonexistent_message_raises(
        self,
        handler: EditMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        owner_jwt: UserJWTData,
    ) -> None:
        command = EditMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=999999,
            new_content="Ghost edit",
        )

        with pytest.raises(NotFoundMessageException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_edit_message_wrong_chat_raises(
        self,
        handler: EditMessageCommandHandler,
        persisted_group_chat: Chat,
        persisted_message: Message,
        owner_jwt: UserJWTData,
    ) -> None:
        command = EditMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            message_id=persisted_message.id,
            new_content="Wrong chat edit",
        )

        with pytest.raises(NotFoundMessageException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_edit_with_too_long_content_raises(
        self,
        handler: EditMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        owner_jwt: UserJWTData,
    ) -> None:

        command = EditMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
            new_content="x" * 4097,
        )

        with pytest.raises(MessageTooLongException):
            await handler.handle(command)
