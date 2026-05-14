from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.update import UpdateChatCommand, UpdateChatCommandHandler
from app.chats.exceptions import AccessDeniedChatException, NotFoundChatException, SlowModeOutOfRangeException
from app.chats.models.chat import Chat
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData
from tests.conftest import MockEventBus



@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
class TestUpdateChatCommand:
    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        mock_event_bus: BaseEventBus,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
    ) -> UpdateChatCommandHandler:
        return UpdateChatCommandHandler(
            sessions=db_session,
            chat_repository=chat_repository,
            access_service=chat_access_service,
            event_bus=mock_event_bus,
        )

    async def test_owner_can_rename_group(
        self,
        handler: UpdateChatCommandHandler,
        chat_repository: ChatRepository,
        group_chat: Chat,
        user_jwt: UserJWTData,
    ) -> None:

        await handler.handle(
            UpdateChatCommand(
                chat_id=group_chat.id,
                name="New Name",
                description="Updated",
                is_public=True,
                user_jwt_data=user_jwt,
            )
        )

        group = await chat_repository.get_by_id(group_chat.id)
        assert group is not None
        assert group.name == "New Name"
        assert group.description == "Updated"
        assert group.is_public is True

    async def test_non_member_cannot_update_chat(
        self,
        handler: UpdateChatCommandHandler,
        group_chat: Chat,
        make_user_jwt
    ) -> None:
        outsider = make_user_jwt(id="99")
        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                UpdateChatCommand(
                    chat_id=group_chat.id,
                    name="Hijacked",
                    description=None,
                    is_public=None,
                    user_jwt_data=outsider,
                )
            )

    async def test_update_slow_mode_out_of_range_raises(
        self,
        handler: UpdateChatCommandHandler,
        group_chat: Chat,
        user_jwt: UserJWTData,
    ) -> None:

        with pytest.raises(SlowModeOutOfRangeException):
            await handler.handle(
                UpdateChatCommand(
                    chat_id=group_chat.id,
                    name="G",
                    description=None,
                    is_public=None,
                    slow_mode_seconds=999_999,
                    user_jwt_data=user_jwt,
                )
            )

    async def test_update_nonexistent_chat_raises(
        self,
        handler: UpdateChatCommandHandler,
        user_jwt: UserJWTData,
    ) -> None:
        with pytest.raises(NotFoundChatException):
            await handler.handle(
                UpdateChatCommand(
                    chat_id=uuid4(),
                    name="X",
                    description=None,
                    is_public=None,
                    user_jwt_data=user_jwt,
                )
            )
