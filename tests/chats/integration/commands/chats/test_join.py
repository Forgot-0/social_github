from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.join import JoinChatCommand, JoinChatCommandHandler
from app.chats.exceptions import (
    AccessDeniedChatException,
    AlreadyMemberException,
    NotFoundChatException,
)
from app.chats.models.chat import Chat, ChatType
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

    async def test_user_joins_public_group_and_gets_member_role(
        self,
        handler: JoinChatCommandHandler,
        public_group_chat: Chat,
        chat_repository: ChatRepository,
        make_user_jwt,
    ) -> None:
        newcomer = make_user_jwt(id="99")

        await handler.handle(JoinChatCommand(chat_id=public_group_chat.id, user_jwt_data=newcomer))

        member = await chat_repository.get_member_chat(chat_id=public_group_chat.id, member_id=99)
        assert member is not None
        assert member.role_id == ChatRolesEnum.MEMBER.value.id

    async def test_cannot_join_private_group(
        self,
        handler: JoinChatCommandHandler,
        group_chat: Chat,
        make_user_jwt,
    ) -> None:
        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                JoinChatCommand(chat_id=group_chat.id, user_jwt_data=make_user_jwt(id="99"))
            )

    async def test_cannot_join_direct_chat(
        self,
        handler: JoinChatCommandHandler,
        direct_chat: Chat,
        make_user_jwt,
    ) -> None:
        outsider = make_user_jwt(id="99")
        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                JoinChatCommand(chat_id=direct_chat.id, user_jwt_data=outsider)
            )

    async def test_already_member_raises_conflict(
        self,
        handler: JoinChatCommandHandler,
        user_jwt: UserJWTData,
        public_group_chat: Chat,
    ) -> None:
        with pytest.raises(AlreadyMemberException):
            await handler.handle(
                JoinChatCommand(chat_id=public_group_chat.id, user_jwt_data=user_jwt)
            )

    async def test_banned_user_can_rejoin_public_chat(
        self,
        handler: JoinChatCommandHandler,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        public_group_chat: Chat,
        make_user_jwt,
    ) -> None:
        target = make_user_jwt(id="2")
        member = await chat_repository.get_member_chat(public_group_chat.id, 2)
        assert member is not None
        member.is_banned = True
        await db_session.commit()

        await handler.handle(JoinChatCommand(chat_id=public_group_chat.id, user_jwt_data=target))

        refreshed = await chat_repository.get_member_chat(public_group_chat.id, 2)
        assert refreshed is not None
        assert refreshed.is_banned is False

    async def test_join_nonexistent_chat_raises_not_found(
        self,
        handler: JoinChatCommandHandler,
        make_user_jwt,
    ) -> None:
        with pytest.raises(NotFoundChatException):
            await handler.handle(
                JoinChatCommand(chat_id=uuid4(), user_jwt_data=make_user_jwt(id="99"))
            )