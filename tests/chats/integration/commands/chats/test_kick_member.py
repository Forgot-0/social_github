import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.kick_member import KickMemberCommand, KickMemberCommandHandler
from app.chats.exceptions import AccessDeniedChatException, NotChatMemberException
from app.chats.models.chat import Chat, KickedChatMemberEvent
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData
from tests.conftest import MockEventBus


@pytest.mark.integration
@pytest.mark.chats
class TestKickMemberCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
        chat_access_service: ChatAccessService,
        mock_event_bus: MockEventBus,
    ) -> KickMemberCommandHandler:
        return KickMemberCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
            chat_access_servise=chat_access_service,
            event_bus=mock_event_bus,
        )

    @pytest.mark.asyncio
    async def test_owner_can_kick_member(
        self,
        handler: KickMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
        member_jwt: UserJWTData,
    ) -> None:
        command = KickMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
        )

        await handler.handle(command)

        kicked = await chat_repository.get_member(
            persisted_group_chat_with_member.id, int(member_jwt.id)
        )
        assert kicked is None

    @pytest.mark.asyncio
    async def test_kick_publishes_event(
        self,
        handler: KickMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        owner_jwt: UserJWTData,
        member_jwt: UserJWTData,
        mock_event_bus: MockEventBus,
    ) -> None:
        command = KickMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
        )

        await handler.handle(command)

        assert len(mock_event_bus.published_events) == 1
        event = mock_event_bus.published_events[0]
        assert isinstance(event, KickedChatMemberEvent)
        assert event.target_user_id == int(member_jwt.id)

    @pytest.mark.asyncio
    async def test_non_member_cannot_kick(
        self,
        handler: KickMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        stranger_jwt: UserJWTData,
        member_jwt: UserJWTData,
    ) -> None:
        command = KickMemberCommand(
            user_jwt_data=stranger_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(member_jwt.id),
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_regular_member_cannot_kick(
        self,
        handler: KickMemberCommandHandler,
        persisted_group_chat_with_member: Chat,
        member_jwt: UserJWTData,
        owner_jwt: UserJWTData,
    ) -> None:
        command = KickMemberCommand(
            user_jwt_data=member_jwt,
            chat_id=persisted_group_chat_with_member.id,
            target_user_id=int(owner_jwt.id),
        )

        with pytest.raises(AccessDeniedChatException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_kick_nonexistent_target_raises(
        self,
        handler: KickMemberCommandHandler,
        persisted_group_chat: Chat,
        owner_jwt: UserJWTData,
    ) -> None:
        command = KickMemberCommand(
            user_jwt_data=owner_jwt,
            chat_id=persisted_group_chat.id,
            target_user_id=99999,
        )

        with pytest.raises(NotChatMemberException):
            await handler.handle(command)

