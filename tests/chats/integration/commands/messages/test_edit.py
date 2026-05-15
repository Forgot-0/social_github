from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.messages.modify import EditMessageCommand, EditMessageCommandHandler
from app.chats.exceptions import AccessDeniedChatException, NotFoundMessageException
from app.chats.models.chat import Chat
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
class TestEditMessageCommand:
    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        message_repository: MessageRepository,
        mock_event_bus: BaseEventBus,
    ) -> EditMessageCommandHandler:
        return EditMessageCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            message_repository=message_repository,
            event_bus=mock_event_bus
        )

    async def test_author_edits_own_message(
        self,
        handler: EditMessageCommandHandler,
        message_repository: MessageRepository,
        group_chat: Chat,
        create_message,
        user_jwt: UserJWTData,
    ) -> None:
        original = await create_message(group_chat, user_jwt, "Original")
        await handler.handle(
            EditMessageCommand(
                user_jwt_data=user_jwt,
                chat_id=group_chat.id,
                message_id=original.id,
                new_content="Edited content",
            )
        )

        msg = await message_repository.get_by_id(original.id)
        assert msg is not None
        assert msg.content == "Edited content"
        assert msg.is_edited is True

    async def test_non_author_cannot_edit(
        self,
        handler: EditMessageCommandHandler,
        group_chat: Chat,
        create_message,
        user_jwt: UserJWTData,
        make_user_jwt,
    ) -> None:
        msg = await create_message(group_chat, make_user_jwt(id="2"), "Original")

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                EditMessageCommand(
                    user_jwt_data=user_jwt,
                    chat_id=group_chat.id,
                    message_id=msg.id,
                    new_content="Hijacked",
                )
            )

    async def test_edit_nonexistent_message_raises(
        self,
        handler: EditMessageCommandHandler,
        group_chat: Chat,
        user_jwt: UserJWTData,
    ) -> None:
        with pytest.raises(NotFoundMessageException):
            await handler.handle(
                EditMessageCommand(
                    user_jwt_data=user_jwt,
                    chat_id=group_chat.id,
                    message_id=uuid4(),
                    new_content="X",
                )
            )

    async def test_edit_message_from_different_chat_raises(
        self,
        handler: EditMessageCommandHandler,
        create_group_chat,
        create_message,
        user_jwt: UserJWTData
    ) -> None:
        chat_a = await create_group_chat([2, 3])
        chat_b = await create_group_chat([2, 3])

        msg_in_a = await create_message(chat_a, user_jwt, "In A")

        with pytest.raises(NotFoundMessageException):
            await handler.handle(
                EditMessageCommand(
                    user_jwt_data=user_jwt,
                    chat_id=chat_b.id,
                    message_id=msg_in_a.id,
                    new_content="Bad edit",
                )
            )
