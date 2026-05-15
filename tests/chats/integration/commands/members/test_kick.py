import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.kick import KickMemberCommand, KickMemberCommandHandler
from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException
from app.chats.models.chat import Chat
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
class TestKickMemberCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
        mock_event_bus: BaseEventBus,
    ) -> KickMemberCommandHandler:
        return KickMemberCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            chat_access_service=chat_access_service,
            event_bus=mock_event_bus
        )

    async def test_owner_kicks_member(
        self,
        handler: KickMemberCommandHandler,
        chat_repository: ChatRepository,
        group_chat: Chat,
        user_jwt: UserJWTData,
    ) -> None:
        await handler.handle(
            KickMemberCommand(
                user_jwt_data=user_jwt,
                chat_id=group_chat.id,
                target_user_id=2,
            )
        )

        kicked = await chat_repository.get_member_chat(group_chat.id, 2)
        assert kicked is None

    async def test_member_cannot_kick_self(
        self,
        handler: KickMemberCommandHandler,
        group_chat: Chat,
        user_jwt: UserJWTData,
    ) -> None:

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                KickMemberCommand(
                    user_jwt_data=user_jwt,
                    chat_id=group_chat.id,
                    target_user_id=1,
                )
            )

    async def test_regular_member_cannot_kick(
        self,
        handler: KickMemberCommandHandler,
        make_user_jwt,
        group_chat: Chat,
    ) -> None:

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                KickMemberCommand(
                    user_jwt_data=make_user_jwt(id="2"),
                    chat_id=group_chat.id,
                    target_user_id=3,
                )
            )

    async def test_kick_nonexistent_target_raises(
        self,
        handler: KickMemberCommandHandler,
        user_jwt: UserJWTData,
        group_chat: Chat,
    ) -> None:
        with pytest.raises(NotChatMemberException):
            await handler.handle(
                KickMemberCommand(
                    user_jwt_data=user_jwt,
                    chat_id=group_chat.id,
                    target_user_id=999,
                )
            )
