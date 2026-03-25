import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.update import UpdateChatCommand, UpdateChatCommandHandler
from app.chats.exceptions import (
    AccessDeniedChatException,
    NotChatMemberException,
    NotFoundChatException,
)
from app.chats.models.chat import Chat
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
class TestUpdateChatCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
    ) -> UpdateChatCommandHandler:
        return UpdateChatCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            chat_access_servise=chat_access_service,
        )

    @pytest.mark.asyncio
    async def test_owner_can_update_name(
        self,
        handler: UpdateChatCommandHandler,
        persisted_group_chat: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = UpdateChatCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            name="New Name",
        )

        await handler.handle(command)

        chat = await chat_repository.get_by_id(persisted_group_chat.id)
        assert chat is not None
        assert chat.name == "New Name"

    @pytest.mark.asyncio
    async def test_owner_can_update_description(
        self,
        handler: UpdateChatCommandHandler,
        persisted_group_chat: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = UpdateChatCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            description="Updated description",
        )

        await handler.handle(command)

        chat = await chat_repository.get_by_id(persisted_group_chat.id)
        assert chat is not None
        assert chat.description == "Updated description"

    @pytest.mark.asyncio
    async def test_owner_can_update_avatar_url(
        self,
        handler: UpdateChatCommandHandler,
        persisted_group_chat: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        url = "https://example.com/avatar.png"
        command = UpdateChatCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            avatar_url=url,
        )

        await handler.handle(command)

        chat = await chat_repository.get_by_id(persisted_group_chat.id)
        assert chat is not None
        assert chat.avatar_url == url

    @pytest.mark.asyncio
    async def test_none_fields_not_overwritten(
        self,
        handler: UpdateChatCommandHandler,
        persisted_group_chat: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        original_name = persisted_group_chat.name

        command = UpdateChatCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            description="Only description changed",
        )

        await handler.handle(command)

        chat = await chat_repository.get_by_id(persisted_group_chat.id)
        assert chat is not None
        assert chat.name == original_name

    @pytest.mark.asyncio
    async def test_non_member_cannot_update(
        self,
        handler: UpdateChatCommandHandler,
        persisted_group_chat: Chat,
        stranger_jwt: UserJWTData,
    ) -> None:
        command = UpdateChatCommand(
            user_jwt_data=stranger_jwt,
            chat_id=persisted_group_chat.id,
            name="Hijacked",
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_regular_member_without_permission_cannot_update(
        self,
        handler: UpdateChatCommandHandler,
        persisted_group_chat_with_member: Chat,
        member_jwt: UserJWTData,
    ) -> None:
        command = UpdateChatCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            name="Hijacked",
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_nonexistent_chat_raises(
        self,
        handler: UpdateChatCommandHandler,
        owner_jwt: UserJWTData,
    ) -> None:
        command = UpdateChatCommand(
            user_jwt_data=owner_jwt,
            chat_id=999999,
            name="Ghost",
        )

        with pytest.raises(NotFoundChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_super_admin_can_update_any_chat(
        self,
        handler: UpdateChatCommandHandler,
        persisted_group_chat: Chat,
        chat_repository: ChatRepository,
        super_admin_user_jwt: UserJWTData,
    ) -> None:
        command = UpdateChatCommand(
            user_jwt_data=super_admin_user_jwt,
            chat_id=persisted_group_chat.id,
            name="Admin Updated",
        )

        await handler.handle(command)

        chat = await chat_repository.get_by_id(persisted_group_chat.id)
        assert chat is not None
        assert chat.name == "Admin Updated"
