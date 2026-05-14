import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.models.chat import Chat, ChatType
from app.chats.repositories.chat import ChatRepository
from app.chats.services.access import ChatAccessService
from app.chats.services.livekit_service import LiveKitService
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


