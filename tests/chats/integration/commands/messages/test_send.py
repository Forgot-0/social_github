import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.messages.send import SendMessageCommand, SendMessageCommandHandler, SendMessageResult
from app.chats.events.messages.sended import SendedMessageEvent
from app.chats.exceptions import (
    AccessDeniedChatException,
    MessageTooLongException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.models.chat import Chat
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData
from tests.conftest import MockEventBus


@pytest.mark.integration
@pytest.mark.chats
class TestSendMessageCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        message_repository: MessageRepository,
        chat_access_service: ChatAccessService,
        mock_event_bus: MockEventBus,
    ) -> SendMessageCommandHandler:
        return SendMessageCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            message_repository=message_repository,
            chat_access_servise=chat_access_service,
            event_bus=mock_event_bus,
        )

    @pytest.mark.asyncio
    async def test_member_can_send_message(
        self,
        handler: SendMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        message_repository: MessageRepository,
        member_jwt: UserJWTData,
    ) -> None:
        command = SendMessageCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            content="Hello everyone!",
        )

        result = await handler.handle(command)

        assert isinstance(result, SendMessageResult)
        assert result.message_id is not None
        assert result.chat_id == persisted_group_chat_with_member.id

        msg = await message_repository.get_by_id(result.message_id)
        assert msg is not None
        assert msg.content == "Hello everyone!"
        assert msg.author_id == int(member_jwt.id)

    @pytest.mark.asyncio
    async def test_owner_can_send_message(
        self,
        handler: SendMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        message_repository: MessageRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = SendMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            content="Owner message",
        )

        result = await handler.handle(command)

        assert result.message_id is not None
        msg = await message_repository.get_by_id(result.message_id)
        assert msg is not None
        assert msg.author_id == int(owner_jwt.id)

    @pytest.mark.asyncio
    async def test_send_publishes_event(
        self,
        handler: SendMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        member_jwt: UserJWTData,
        mock_event_bus: MockEventBus,
    ) -> None:
        command = SendMessageCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            content="Event test",
        )

        await handler.handle(command)

        assert len(mock_event_bus.published_events) == 1
        event = mock_event_bus.published_events[0]
        assert isinstance(event, SendedMessageEvent)
        assert event.sender_id == int(member_jwt.id)

    @pytest.mark.asyncio
    async def test_non_member_cannot_send(
        self,
        handler: SendMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        stranger_jwt: UserJWTData,
    ) -> None:
        command = SendMessageCommand(
            user_jwt_data=stranger_jwt,
            chat_id=persisted_group_chat_with_member.id,
            content="Intruder message",
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_chat_raises(
        self,
        handler: SendMessageCommandHandler,
        owner_jwt: UserJWTData,
    ) -> None:
        command = SendMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=999999,
            content="Ghost message",
        )

        with pytest.raises(NotFoundChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_send_message_updates_chat_last_activity(
        self,
        handler: SendMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        chat_repository: ChatRepository,
        member_jwt: UserJWTData,
    ) -> None:
        command = SendMessageCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            content="Activity test",
        )

        result = await handler.handle(command)

        chat = await chat_repository.get_by_id(persisted_group_chat_with_member.id)
        assert chat is not None
        assert chat.last_activity_at is not None
        assert chat.last_message_id == result.message_id

    @pytest.mark.asyncio
    async def test_send_reply_message(
        self,
        handler: SendMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message,
        message_repository: MessageRepository,
        member_jwt: UserJWTData,
    ) -> None:
        command = SendMessageCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            content="Reply message",
            reply_to_id=persisted_message.id,
        )

        result = await handler.handle(command)

        msg = await message_repository.get_by_id(result.message_id)
        assert msg is not None
        assert msg.reply_to_id == persisted_message.id

    @pytest.mark.asyncio
    async def test_send_too_long_message_raises(
        self,
        handler: SendMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        member_jwt: UserJWTData,
    ) -> None:

        command = SendMessageCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            content="x" * 4097,
        )

        with pytest.raises(MessageTooLongException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_viewer_cannot_send_message(
        self,
        db_session: AsyncSession,
        handler: SendMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        chat_repository: ChatRepository,
        make_user_jwt,
    ) -> None:
        viewer_id = 777
        await chat_repository.add_member(
            chat_id=persisted_group_chat_with_member.id,
            user_id=viewer_id,
            role_id=6,
        )
        await db_session.flush()

        viewer_jwt = make_user_jwt(id=str(viewer_id), username="viewer")
        command = SendMessageCommand(
            user_jwt_data=viewer_jwt,
            chat_id=persisted_group_chat_with_member.id,
            content="Viewer trying to speak",
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)
