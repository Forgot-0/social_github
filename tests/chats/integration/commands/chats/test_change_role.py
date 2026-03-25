import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.change_role import ChangeMemberRoleCommand, ChangeMemberRoleCommandHandler
from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException
from app.chats.models.chat import Chat
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
class TestChangeMemberRoleCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
    ) -> ChangeMemberRoleCommandHandler:
        return ChangeMemberRoleCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            chat_access_servise=chat_access_service,
        )

    @pytest.mark.asyncio
    async def test_owner_can_change_member_role(
        self,
        handler: ChangeMemberRoleCommandHandler,
        persisted_group_chat_with_member: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
        member_jwt: UserJWTData,
    ) -> None:
        command = ChangeMemberRoleCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
            role_id=2,
        )

        await handler.handle(command)

        member = await chat_repository.get_member(
            persisted_group_chat_with_member.id, int(member_jwt.id)
        )
        assert member is not None
        assert member.role_id == 2

    @pytest.mark.asyncio
    async def test_regular_member_cannot_change_role(
        self,
        handler: ChangeMemberRoleCommandHandler,
        persisted_group_chat_with_member: Chat,
        member_jwt: UserJWTData,
        owner_jwt: UserJWTData,
    ) -> None:
        command = ChangeMemberRoleCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(owner_jwt.id),
            role_id=6,
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_change_role_of_nonexistent_target_raises(
        self,
        handler: ChangeMemberRoleCommandHandler,
        persisted_group_chat: Chat,
        owner_jwt: UserJWTData,
    ) -> None:
        command = ChangeMemberRoleCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            target_user_id=99999,
            role_id=5,
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_super_admin_can_change_any_role(
        self,
        handler: ChangeMemberRoleCommandHandler,
        persisted_group_chat_with_member: Chat,
        chat_repository: ChatRepository,
        super_admin_user_jwt: UserJWTData,
        member_jwt: UserJWTData,
    ) -> None:
        command = ChangeMemberRoleCommand(
            user_jwt_data=super_admin_user_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
            role_id=6,
        )

        await handler.handle(command)

        member = await chat_repository.get_member(
            persisted_group_chat_with_member.id, int(member_jwt.id)
        )
        assert member is not None
        assert member.role_id == 6
