import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.ban_member import BanMemberCommand, BanMemberCommandHandler
from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException
from app.chats.models.chat import Chat
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData
from tests.chats.conftest import MockConnectionManager


@pytest.mark.integration
@pytest.mark.chats
class TestBanMemberCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
        mock_connection_manager: MockConnectionManager,
    ) -> BanMemberCommandHandler:
        return BanMemberCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            chat_access_servise=chat_access_service,
            connection_manager=mock_connection_manager,
        )

    @pytest.mark.asyncio
    async def test_owner_can_ban_member(
        self,
        handler: BanMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
        member_jwt: UserJWTData,
    ) -> None:
        command = BanMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
            ban=True,
        )

        await handler.handle(command)

        member = await chat_repository.get_member(
            persisted_group_chat_with_member.id, int(member_jwt.id)
        )
        assert member is not None
        assert member.is_banned is True

    @pytest.mark.asyncio
    async def test_ban_disconnects_ws(
        self,
        handler: BanMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        owner_jwt: UserJWTData,
        member_jwt: UserJWTData,
        mock_connection_manager: MockConnectionManager,
    ) -> None:
        command = BanMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
            ban=True,
        )

        await handler.handle(command)

        assert len(mock_connection_manager.unbind_calls) == 1

    @pytest.mark.asyncio
    async def test_unban_reconnects_ws(
        self,
        handler: BanMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
        member_jwt: UserJWTData,
        mock_connection_manager: MockConnectionManager,
    ) -> None:
        ban_cmd = BanMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
            ban=True,
        )
        await handler.handle(ban_cmd)

        unban_cmd = BanMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
            ban=False,
        )
        await handler.handle(unban_cmd)

        member = await chat_repository.get_member(
            persisted_group_chat_with_member.id, int(member_jwt.id)
        )
        assert member is not None
        assert member.is_banned is False
        assert len(mock_connection_manager.bind_calls) == 1

    @pytest.mark.asyncio
    async def test_non_member_cannot_ban(
        self,
        handler: BanMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        stranger_jwt: UserJWTData,
        member_jwt: UserJWTData,
    ) -> None:
        command = BanMemberCommand(
            user_jwt_data=stranger_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
            ban=True,
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_member_without_permission_cannot_ban(
        self,
        handler: BanMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        member_jwt: UserJWTData,
        owner_jwt: UserJWTData,
    ) -> None:
        command = BanMemberCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(owner_jwt.id),
            ban=True,
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_ban_nonexistent_target_raises(
        self,
        handler: BanMemberCommandHandler,
        persisted_group_chat: Chat,
        owner_jwt: UserJWTData,
    ) -> None:
        command = BanMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            target_user_id=99999,
            ban=True,
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)
