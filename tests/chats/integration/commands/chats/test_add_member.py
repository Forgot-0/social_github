import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.add_member import AddMemberCommand, AddMemberCommandHandler
from app.chats.config import chat_config
from app.chats.exceptions import (
    AccessDeniedChatException,
    AlreadyMemberException,
    MemberLimitExceededException,
    NotChatMemberException,
)
from app.chats.models.chat import Chat, ChatType
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData
from tests.chats.conftest import MockConnectionManager


@pytest.mark.integration
@pytest.mark.chats
class TestAddMemberCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
        mock_connection_manager: MockConnectionManager,
    ) -> AddMemberCommandHandler:
        return AddMemberCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            chat_access_servise=chat_access_service,
            connection_manager=mock_connection_manager,
        )

    @pytest.mark.asyncio
    async def test_owner_can_add_member(
        self,
        handler: AddMemberCommandHandler,
        persisted_group_chat: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        new_user_id = 200

        command = AddMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            target_user_id=new_user_id,
            role_id=5,
        )

        await handler.handle(command)

        member = await chat_repository.get_member(persisted_group_chat.id, new_user_id)
        assert member is not None
        assert member.role_id == 5

    @pytest.mark.asyncio
    async def test_add_member_binds_ws_connection(
        self,
        handler: AddMemberCommandHandler,
        persisted_group_chat: Chat,
        owner_jwt: UserJWTData,
        mock_connection_manager: MockConnectionManager,
    ) -> None:
        command = AddMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            target_user_id=201,
            role_id=5,
        )

        await handler.handle(command)

        assert len(mock_connection_manager.bind_calls) == 1

    @pytest.mark.asyncio
    async def test_non_member_cannot_add(
        self,
        handler: AddMemberCommandHandler,
        persisted_group_chat: Chat,
        stranger_jwt: UserJWTData,
    ) -> None:
        command = AddMemberCommand(
            user_jwt_data=stranger_jwt,
            chat_id=persisted_group_chat.id,
            target_user_id=202,
            role_id=5,
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_regular_member_without_invite_permission_cannot_add(
        self,
        handler: AddMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        member_jwt: UserJWTData,
    ) -> None:
        command = AddMemberCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=203,
            role_id=5,
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_add_already_existing_member_raises(
        self,
        handler: AddMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        owner_jwt: UserJWTData,
        member_jwt: UserJWTData,
    ) -> None:
        command = AddMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
            role_id=5,
        )

        with pytest.raises(AlreadyMemberException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_add_to_nonexistent_chat_raises(
        self,
        handler: AddMemberCommandHandler,
        owner_jwt: UserJWTData,
    ) -> None:
        command = AddMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=999999,
            target_user_id=204,
            role_id=5,
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_add_member_when_limit_reached_raises(
        self,
        db_session: AsyncSession,
        handler: AddMemberCommandHandler,
        owner_jwt: UserJWTData,
    ) -> None:
        member_ids = list(range(5000, 5000 + chat_config.MAX_MEMBERS - 1))
        chat = Chat.create(
            created_by=int(owner_jwt.id),
            members_ids=member_ids,
            chat_type=ChatType.GROUP,
            name="Full chat",
        )
        db_session.add(chat)
        await db_session.flush()

        command = AddMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=chat.id,
            target_user_id=6000,
            role_id=5,
        )

        with pytest.raises(MemberLimitExceededException):
            await handler.handle(command)
