import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.models.chat import Chat, ChatType
from app.chats.models.message import Message
from app.chats.repositories.attachment import AttachmentRepository
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.livekit_service import LiveKitService
from app.chats.services.slow_mode import SlowModeService
from app.core.services.auth.dto import UserJWTData
from tests.chats.integration.mock import StubLiveKitService


@pytest.fixture
def livekit() -> LiveKitService:
    return StubLiveKitService(url="ws://test", api_key="k", api_secret="s")

@pytest.fixture
def chat_repository(redis_client, db_session) -> ChatRepository:
    return ChatRepository(redis=redis_client, session=db_session)

@pytest.fixture
def chat_access_service(rbac_manager) -> ChatAccessService:
    return ChatAccessService(rbac_manager=rbac_manager)

@pytest.fixture
def message_repository(db_session: AsyncSession) -> MessageRepository:
    return MessageRepository(session=db_session)

@pytest.fixture
def attachment_repository(db_session: AsyncSession, redis_client) -> AttachmentRepository:
    return AttachmentRepository(session=db_session, redis=redis_client)

@pytest.fixture
def read_repository(db_session: AsyncSession) -> ReadReceiptRepository:
    return ReadReceiptRepository(session=db_session)

@pytest.fixture
def slow_mode_service(redis_client, chat_access_service: ChatAccessService) -> SlowModeService:
    return SlowModeService(redis=redis_client, access_service=chat_access_service)


@pytest.fixture
async def group_chat(
    db_session: AsyncSession,
    user_jwt: UserJWTData,
) -> Chat:
    chat = Chat.create(
        created_by=int(user_jwt.id),
        members_ids=[2, 3],
        chat_type=ChatType.GROUP,
        name="New Chat",
        is_public=False
    )
    db_session.add(chat)
    await db_session.commit()
    await db_session.refresh(chat)
    return chat



@pytest.fixture
async def create_group_chat(
    db_session: AsyncSession,
    user_jwt: UserJWTData,
) :
    async def create(members: list[int], slow_mode: int=0, admin_only: bool=False) -> Chat:
        chat = Chat.create(
            created_by=int(user_jwt.id),
            members_ids=members,
            chat_type=ChatType.GROUP,
            name="New Chat",
            is_public=False,
            slow_mode_seconds=slow_mode,
            admin_only=admin_only
        )
        db_session.add(chat)
        await db_session.commit()
        await db_session.refresh(chat)
        return chat
    return create


@pytest.fixture
async def create_message(
    db_session: AsyncSession,
):
    async def create(chat: Chat, user_jwt: UserJWTData, content: str | None, forward_msg: Message | None=None):
        msg = Message.create(
            sender_id=int(user_jwt.id),
            chat_id=chat.id,
            content=content,
            seq=chat.seq_counter+1,
            forwarded_from_author_id=forward_msg.author_id if forward_msg else None,
            forwarded_from_chat_id=forward_msg.chat_id if forward_msg else None,
            forwarded_from_message_id=forward_msg.id if forward_msg else None
        )
        chat.seq_counter += 1
        db_session.add(msg)
        await db_session.commit()
        await db_session.refresh(msg)
        return msg
    return create
