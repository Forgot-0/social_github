import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.messages.delete import DeleteMessageCommand, DeleteMessageCommandHandler
from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundMessageException,
)
from app.chats.models.chat import Chat
from app.chats.models.message import DeletedMessageEvent, Message
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData
from tests.conftest import MockEventBus


@pytest.mark.integration
@pytest.mark.chats
class TestDeleteMessageCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        message_repository: MessageRepository,
        chat_access_service: ChatAccessService,
        mock_event_bus: MockEventBus,
    ) -> DeleteMessageCommandHandler:
        return DeleteMessageCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            message_repository=message_repository,
            chat_access_servise=chat_access_service,
            event_bus=mock_event_bus,
        )

    @pytest.mark.asyncio
    async def test_author_can_delete_own_message(
        self,
        handler: DeleteMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        message_repository: MessageRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = DeleteMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )

        await handler.handle(command)

        msg = await message_repository.get_by_id(persisted_message.id)
        assert msg is None

    @pytest.mark.asyncio
    async def test_delete_publishes_event(
        self,
        handler: DeleteMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        owner_jwt: UserJWTData,
        mock_event_bus: MockEventBus,
    ) -> None:
        command = DeleteMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )

        await handler.handle(command)

        assert len(mock_event_bus.published_events) == 1
        event = mock_event_bus.published_events[0]
        assert isinstance(event, DeletedMessageEvent)
        assert event.message_id == persisted_message.id

    @pytest.mark.asyncio
    async def test_non_author_without_permission_cannot_delete(
        self,
        handler: DeleteMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        member_jwt: UserJWTData,
    ) -> None:
        command = DeleteMessageCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_owner_can_delete_any_message(
        self,
        db_session: AsyncSession,
        handler: DeleteMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        message_repository: MessageRepository,
        owner_jwt: UserJWTData,
        member_jwt: UserJWTData,
    ) -> None:
        msg = Message.create(
            sender_id=int(member_jwt.id),
            chat_id=persisted_group_chat_with_member.id,
            content="Member message",
        )
        db_session.add(msg)
        await db_session.flush()

        command = DeleteMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=msg.id,
        )

        await handler.handle(command)

        deleted = await message_repository.get_by_id(msg.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_non_member_cannot_delete(
        self,
        handler: DeleteMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        stranger_jwt: UserJWTData,
    ) -> None:
        command = DeleteMessageCommand(
            user_jwt_data=stranger_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_message_raises(
        self,
        handler: DeleteMessageCommandHandler,
        persisted_group_chat_with_member: Chat,
        owner_jwt: UserJWTData,
    ) -> None:
        command = DeleteMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=999999,
        )

        with pytest.raises(NotFoundMessageException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_delete_message_from_wrong_chat_raises(
        self,
        handler: DeleteMessageCommandHandler,
        persisted_group_chat: Chat,
        persisted_message: Message,
        owner_jwt: UserJWTData,
    ) -> None:
        command = DeleteMessageCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            message_id=persisted_message.id,
        )

        with pytest.raises(NotFoundMessageException):
            await handler.handle(command)
