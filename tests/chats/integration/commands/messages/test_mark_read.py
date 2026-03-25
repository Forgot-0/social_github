import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.messages.mark_read import MarkAsReadCommand, MarkAsReadCommandHandler
from app.chats.exceptions import NotChatMemberException
from app.chats.models.chat import Chat
from app.chats.models.message import Message
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.core.services.auth.dto import UserJWTData
from tests.chats.conftest import MockConnectionManager


@pytest.mark.integration
@pytest.mark.chats
class TestMarkAsReadCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        read_receipt_repository: ReadReceiptRepository,
        mock_connection_manager: MockConnectionManager,
    ) -> MarkAsReadCommandHandler:
        return MarkAsReadCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            read_receipt_repository=read_receipt_repository,
            connection_manager=mock_connection_manager,
        )

    @pytest.mark.asyncio
    async def test_member_can_mark_as_read(
        self,
        handler: MarkAsReadCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        read_receipt_repository: ReadReceiptRepository,
        member_jwt: UserJWTData,
    ) -> None:
        command = MarkAsReadCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )

        await handler.handle(command)

        last_read = await read_receipt_repository.get_last_read(
            int(member_jwt.id), persisted_group_chat_with_member.id
        )
        assert last_read == persisted_message.id

    @pytest.mark.asyncio
    async def test_mark_as_read_resets_unread_count(
        self,
        handler: MarkAsReadCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        read_receipt_repository: ReadReceiptRepository,
        member_jwt: UserJWTData,
    ) -> None:
        command = MarkAsReadCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )

        await handler.handle(command)

        unread = await read_receipt_repository.get_unread_count(
            int(member_jwt.id), persisted_group_chat_with_member.id
        )
        assert unread == 0

    @pytest.mark.asyncio
    async def test_mark_as_read_publishes_to_ws(
        self,
        handler: MarkAsReadCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        mock_connection_manager: MockConnectionManager,
        member_jwt: UserJWTData,
    ) -> None:
        command = MarkAsReadCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )

        await handler.handle(command)

        assert len(mock_connection_manager.publish_bulk_calls) == 1
        call = mock_connection_manager.publish_bulk_calls[0]
        assert call["payload"]["type"] == "messages_read"

    @pytest.mark.asyncio
    async def test_non_member_cannot_mark_read(
        self,
        handler: MarkAsReadCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        stranger_jwt: UserJWTData,
    ) -> None:
        command = MarkAsReadCommand(
            user_jwt_data=stranger_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_mark_as_read_idempotent_for_older_message(
        self,
        handler: MarkAsReadCommandHandler,
        persisted_group_chat_with_member: Chat,
        persisted_message: Message,
        read_receipt_repository: ReadReceiptRepository,
        member_jwt: UserJWTData,
    ) -> None:
        command_new = MarkAsReadCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id + 100,
        )
        await handler.handle(command_new)

        command_old = MarkAsReadCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            message_id=persisted_message.id,
        )
        await handler.handle(command_old)

        last_read = await read_receipt_repository.get_last_read(
            int(member_jwt.id), persisted_group_chat_with_member.id
        )
        assert last_read == persisted_message.id + 100
