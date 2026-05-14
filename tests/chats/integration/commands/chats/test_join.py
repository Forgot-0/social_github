from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.join import JoinChatCommand, JoinChatCommandHandler
from app.chats.exceptions import AccessDeniedChatException, AlreadyMemberException, NotFoundChatException
from app.chats.models.chat import Chat
from app.chats.models.permission import ChatRolesEnum
from app.chats.repositories.chat import ChatRepository
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
class TestJoinChatCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        mock_event_bus: BaseEventBus,
        chat_repository: ChatRepository,
    ) -> JoinChatCommandHandler:
        return JoinChatCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            event_bus=mock_event_bus,
        )

    async def test_user_joins_public_group(
        self,
        handler: JoinChatCommandHandler,
        group_chat: Chat,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        make_user_jwt,
    ) -> None:
        group_chat.is_public = True
        await db_session.commit()
        await handler.handle(JoinChatCommand(chat_id=group_chat.id, user_jwt_data=make_user_jwt(id="99")))

        member = await chat_repository.get_member_chat(chat_id=group_chat.id, member_id=99)
        assert member is not None
        assert member.role_id == ChatRolesEnum.MEMBER.value.id

    async def test_cannot_join_private_chat(
        self,
        handler: JoinChatCommandHandler,
        group_chat: Chat,
        make_user_jwt
    ) -> None:
        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                JoinChatCommand(chat_id=group_chat.id, user_jwt_data=make_user_jwt(id="99"))
            )

    async def test_cannot_join_direct_chat(
        self,
        handler: JoinChatCommandHandler,
        user_jwt: UserJWTData,
        group_chat: Chat,
    ) -> None:
        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                JoinChatCommand(chat_id=group_chat.id, user_jwt_data=user_jwt)
            )

    async def test_already_member_raises(
        self,
        handler: JoinChatCommandHandler,
        user_jwt: UserJWTData,
        group_chat: Chat,
        db_session: AsyncSession,
    ) -> None:
        group_chat.is_public = True
        await db_session.commit()

        with pytest.raises(AlreadyMemberException):
            await handler.handle(
                JoinChatCommand(chat_id=group_chat.id, user_jwt_data=user_jwt)
            )

    async def test_join_nonexistent_chat_raises(
        self,
        handler: JoinChatCommandHandler,
        user_jwt: UserJWTData
    ) -> None:
        with pytest.raises(NotFoundChatException):
            await handler.handle(
                JoinChatCommand(chat_id=uuid4(), user_jwt_data=user_jwt)
            )
