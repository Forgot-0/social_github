import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.leave import LeaveChatCommand, LeaveChatCommandHandler
from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException
from app.chats.models.chat import Chat
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
class TestLeaveChatCommand:
    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        mock_event_bus: BaseEventBus,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
    ) -> LeaveChatCommandHandler:
        return LeaveChatCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            access_service=chat_access_service,
            event_bus=mock_event_bus,
        )

    async def test_member_can_leave_group(
        self,
        group_chat: Chat,
        handler: LeaveChatCommandHandler,
        chat_repository: ChatRepository,
        make_user_jwt
    ) -> None: 
        await handler.handle(LeaveChatCommand(chat_id=group_chat.id, user_jwt_data=make_user_jwt(id="2")))

        member = await chat_repository.get_member_chat(chat_id=group_chat.id, member_id=2)
        assert member is None

        chat = await chat_repository.get_by_id(chat_id=group_chat.id)
        assert chat is not None
        assert chat.member_count == 2

    async def test_owner_cannot_leave_own_group(
        self,
        group_chat: Chat,
        user_jwt: UserJWTData,
        handler: LeaveChatCommandHandler,
    ) -> None: 
        with pytest.raises(AccessDeniedChatException):
            await handler.handle(LeaveChatCommand(chat_id=group_chat.id, user_jwt_data=user_jwt))

    async def test_non_member_cannot_leave(
        self,
        group_chat: Chat,
        handler: LeaveChatCommandHandler,
        make_user_jwt
    ) -> None: 
        with pytest.raises(NotChatMemberException):
            await handler.handle(
                LeaveChatCommand(chat_id=group_chat.id, user_jwt_data=make_user_jwt(id="999"))
            )
