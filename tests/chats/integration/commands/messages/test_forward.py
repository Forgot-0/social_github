from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.messages.forward import ForwardMessageCommand, ForwardMessageCommandHandler
from app.chats.exceptions import NotChatMemberException, NotFoundMessageException
from app.chats.models.message import MessageType
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.slow_mode import SlowModeService
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
class TestForwardMessageCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
        message_repository: MessageRepository,
        attachment_repository: AttachmentRepository,
        slow_mode_service: SlowModeService,
        mock_event_bus: BaseEventBus,
    ) -> ForwardMessageCommandHandler:
        return ForwardMessageCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            chat_access_service=chat_access_service,
            message_repository=message_repository,
            attachment_repository=attachment_repository,
            slow_mode_service=slow_mode_service,
            event_bus=mock_event_bus
        )

    async def test_forward_message_to_another_chat(
        self,
        handler: ForwardMessageCommandHandler,
        create_group_chat,
        create_message,
        user_jwt: UserJWTData
    ) -> None:
        src = await create_group_chat([2, 3])
        tgt = await create_group_chat([2, 3])

        original = await create_message(src, user_jwt, "In A")

        fwd = await handler.handle(
            ForwardMessageCommand(
                user_jwt_data=user_jwt,
                source_chat_id=src.id,
                source_message_id=original.id,
                target_chat_id=tgt.id,
            )
        )

        assert fwd.type == MessageType.FORWARD
        assert fwd.forwarded_from_message_id == original.id
        assert fwd.chat_id == tgt.id

    async def test_forward_carries_original_author(
        self,
        handler: ForwardMessageCommandHandler,
        create_group_chat,
        create_message,
        user_jwt: UserJWTData,
        make_user_jwt
    ) -> None:
        src = await create_group_chat([2, 3])
        tgt = await create_group_chat([2, 3])

        original = await create_message(src, make_user_jwt(id="2"), "Original")

        fwd = await handler.handle(
            ForwardMessageCommand(
                user_jwt_data=user_jwt,
                source_chat_id=src.id,
                source_message_id=original.id,
                target_chat_id=tgt.id,
            )
        )

        assert fwd.forwarded_from_author_id == 2

    async def test_forward_nonexistent_source_raises(
        self,
        handler: ForwardMessageCommandHandler,
        create_group_chat,
        user_jwt: UserJWTData,
    ) -> None:
        src = await create_group_chat([2, 3])
        tgt = await create_group_chat([2, 3])

        with pytest.raises(NotFoundMessageException):
            await handler.handle(
                ForwardMessageCommand(
                    user_jwt_data=user_jwt,
                    source_chat_id=src.id,
                    source_message_id=uuid4(),
                    target_chat_id=tgt.id,
                )
            )

    async def test_outsider_cannot_forward_from_private_chat(
        self,
        handler: ForwardMessageCommandHandler,
        create_group_chat,
        create_message,
        user_jwt: UserJWTData,
        make_user_jwt
    ) -> None:
        src = await create_group_chat([2])
        tgt = await create_group_chat([3])

        original = await create_message(src, user_jwt, "Test")

        with pytest.raises(NotChatMemberException):
            await handler.handle(
                ForwardMessageCommand(
                    user_jwt_data=make_user_jwt(id="3"),
                    source_chat_id=src.id,
                    source_message_id=original.id,
                    target_chat_id=tgt.id,
                )
            )
