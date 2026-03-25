import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.commands.chats.create import CreateChatCommand, CreateChatCommandHandler
from app.chats.exceptions import MemberLimitExceededException
from app.chats.models.chat import ChatType
from app.chats.repositories.chat import ChatRepository
from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.chats
class TestCreateChatCommand:

    @pytest.fixture
    def handler(
        self,
        db_session: AsyncSession,
        chat_repository: ChatRepository,
    ) -> CreateChatCommandHandler:
        return CreateChatCommandHandler(
            session=db_session,
            chat_repository=chat_repository,
        )

    @pytest.mark.asyncio
    async def test_create_group_chat_success(
        self,
        handler: CreateChatCommandHandler,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.GROUP,
            name="My Group",
            description="A test group",
            is_public=False,
            member_ids={21, 22},
        )

        chat_id = await handler.handle(command)

        assert chat_id is not None
        chat = await chat_repository.get_by_id(chat_id, with_members=True)
        assert chat is not None
        assert chat.name == "My Group"
        assert chat.type == ChatType.GROUP
        assert len(chat.members) == 3

    @pytest.mark.asyncio
    async def test_create_group_chat_no_members(
        self,
        handler: CreateChatCommandHandler,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.GROUP,
            name="Solo Group",
            member_ids=set(),
        )

        chat_id = await handler.handle(command)
        chat = await chat_repository.get_by_id(chat_id, with_members=True)
        assert chat is not None
        assert len(chat.members) == 1

    @pytest.mark.asyncio
    async def test_create_group_chat_is_public(
        self,
        handler: CreateChatCommandHandler,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.GROUP,
            name="Public Group",
            is_public=True,
            member_ids=set(),
        )

        chat_id = await handler.handle(command)
        chat = await chat_repository.get_by_id(chat_id)
        assert chat is not None
        assert chat.is_public is True

    @pytest.mark.asyncio
    async def test_create_group_chat_creator_is_owner_role(
        self,
        handler: CreateChatCommandHandler,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.GROUP,
            name="Test",
            member_ids={30},
        )

        chat_id = await handler.handle(command)
        chat = await chat_repository.get_by_id(chat_id, with_members=True)
        assert chat is not None
        creator_member = next(
            m for m in chat.members if m.user_id == int(owner_jwt.id)
        )
        assert creator_member.role_id == 1

    @pytest.mark.asyncio
    async def test_create_group_chat_members_have_member_role(
        self,
        handler: CreateChatCommandHandler,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.GROUP,
            name="Test",
            member_ids={31},
        )

        chat_id = await handler.handle(command)
        chat = await chat_repository.get_by_id(chat_id, with_members=True)

        assert chat is not None
        regular = next(m for m in chat.members if m.user_id == 31)
        assert regular.role_id == 5

    @pytest.mark.asyncio
    async def test_create_direct_chat_success(
        self,
        handler: CreateChatCommandHandler,
        chat_repository: ChatRepository,
        owner_jwt: UserJWTData,
    ) -> None:
        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.DIRECT,
            member_ids={50},
        )

        chat_id = await handler.handle(command)
        chat = await chat_repository.get_by_id(chat_id, with_members=True)
        assert chat is not None
        assert chat.type == ChatType.DIRECT
        assert len(chat.members) == 2

    @pytest.mark.asyncio
    async def test_create_direct_chat_wrong_member_count_raises(
        self,
        handler: CreateChatCommandHandler,
        owner_jwt: UserJWTData,
    ) -> None:
        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.DIRECT,
            member_ids={51, 52},
        )

        with pytest.raises(MemberLimitExceededException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_create_direct_chat_no_members_raises(
        self,
        handler: CreateChatCommandHandler,
        owner_jwt: UserJWTData,
    ) -> None:
        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.DIRECT,
            member_ids=set(),
        )

        with pytest.raises(MemberLimitExceededException):
            await handler.handle(command)


    @pytest.mark.asyncio
    async def test_create_group_too_many_members_raises(
        self,
        handler: CreateChatCommandHandler,
        owner_jwt: UserJWTData,
    ) -> None:
        from app.chats.config import chat_config

        too_many = set(range(1000, 1000 + chat_config.MAX_MEMBERS + 1))

        command = CreateChatCommand(
            user_jwt_data=owner_jwt,
            chat_type=ChatType.GROUP,
            name="Too big",
            member_ids=too_many,
        )

        with pytest.raises(MemberLimitExceededException):
            await handler.handle(command)
