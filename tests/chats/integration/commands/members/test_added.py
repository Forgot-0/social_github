from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.add_member import AddMemberCommand, AddMemberCommandHandler
from app.chats.exceptions import AccessDeniedChatException, AlreadyMemberException, NotChatMemberException, NotFoundChatException
from app.chats.models.chat import Chat
from app.chats.models.permission import ChatRolesEnum
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.ws import ChatConnectionManager
from app.core.events.service import BaseEventBus
from app.core.services.auth.dto import UserJWTData

@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
class TestAddMemberCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
        mock_event_bus: BaseEventBus,
    ) -> AddMemberCommandHandler:
        return AddMemberCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            chat_access_service=chat_access_service,
            event_bus=mock_event_bus
        )

    async def test_owner_adds_new_member(
        self,
        db_session: AsyncSession,
        handler: AddMemberCommandHandler,
        chat_repository: ChatRepository,
        user_jwt: UserJWTData,
        group_chat: Chat
    ) -> None:
        await handler.handle(
            AddMemberCommand(
                user_jwt_data=user_jwt,
                chat_id=group_chat.id,
                target_user_id=99,
                role_id=5,
            )
        )
        await db_session.commit()

        member = await chat_repository.get_member_chat(group_chat.id, 99)
        assert member is not None
        assert member.role_id == 5

    async def test_add_already_existing_member_raises(
        self,
        handler: AddMemberCommandHandler,
        user_jwt: UserJWTData,
        group_chat: Chat
    ) -> None:

        with pytest.raises(AlreadyMemberException):
            await handler.handle(
                AddMemberCommand(
                    user_jwt_data=user_jwt,
                    chat_id=group_chat.id,
                    target_user_id=2,
                    role_id=ChatRolesEnum.MEMBER.value.id,
                )
            )

    async def test_regular_member_cannot_add_without_permission(
        self,
        handler: AddMemberCommandHandler,
        make_user_jwt,
        group_chat: Chat
    ) -> None: 
        with pytest.raises(AccessDeniedChatException):
            await handler.handle(
                AddMemberCommand(
                    user_jwt_data=make_user_jwt(id="2"),
                    chat_id=group_chat.id,
                    target_user_id=3,
                    role_id=ChatRolesEnum.MEMBER.value.id,
                )
            )

    async def test_add_to_nonexistent_chat_raises(
        self,
        handler: AddMemberCommandHandler,
        user_jwt: UserJWTData,
    ) -> None:
        with pytest.raises(NotFoundChatException):
            await handler.handle(
                AddMemberCommand(
                    user_jwt_data=user_jwt,
                    chat_id=uuid4(),
                    target_user_id=50,
                    role_id=5,
                )
            )

    async def test_non_member_requester_cannot_add(
        self,
        handler: AddMemberCommandHandler,
        make_user_jwt,
        group_chat: Chat
    ) -> None:
        with pytest.raises(NotChatMemberException):
            await handler.handle(
                AddMemberCommand(
                    user_jwt_data=make_user_jwt(id="999"),
                    chat_id=group_chat.id,
                    target_user_id=50,
                    role_id=5,
                )
            )
