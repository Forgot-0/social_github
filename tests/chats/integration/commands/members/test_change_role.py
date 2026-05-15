import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.change_role import ChangeMemberRoleCommand, ChangeMemberRoleCommandHandler
from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException
from app.chats.models.chat import Chat
from app.chats.models.permission import ChatRolesEnum
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
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
            chat_access_service=chat_access_service,
        )

    async def test_owner_promotes_member_to_admin(
        self,
        handler: ChangeMemberRoleCommandHandler,
        chat_repository: ChatRepository,
        user_jwt: UserJWTData,
        group_chat: Chat
    ) -> None:
        await handler.handle(
            ChangeMemberRoleCommand(
                user_jwt_data=user_jwt,
                chat_id=group_chat.id,
                target_user_id=2,
                role_id=ChatRolesEnum.ADMIN.value.id,
            )
        )

        member = await chat_repository.get_member_chat(group_chat.id, 2)
        assert member is not None
        assert member.role_id == ChatRolesEnum.ADMIN.value.id

    async def test_member_cannot_change_role_of_higher_level(
        self,
        handler: ChangeMemberRoleCommandHandler,
        make_user_jwt,
        group_chat: Chat,
    ) -> None:
        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                ChangeMemberRoleCommand(
                    user_jwt_data=make_user_jwt(id="2"),
                    chat_id=group_chat.id,
                    target_user_id=1,
                    role_id=ChatRolesEnum.MEMBER.value.id,
                )
            )

    async def test_change_role_of_nonexistent_member_raises(
        self,
        handler: ChangeMemberRoleCommandHandler,
        user_jwt: UserJWTData,
        group_chat: Chat,
    ) -> None:
        with pytest.raises(NotChatMemberException):
            await handler.handle(
                ChangeMemberRoleCommand(
                    user_jwt_data=user_jwt,
                    chat_id=group_chat.id,
                    target_user_id=999,
                    role_id=ChatRolesEnum.MEMBER.value.id,
                )
            )
