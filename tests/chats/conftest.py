from dataclasses import dataclass, field
from typing import Any

import pytest
import pytest_asyncio
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.models.chat import Chat, ChatType
from app.chats.models.message import Message, MessageType
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.repositories.reads import ReadReceiptRepository
from app.chats.services.access import ChatAccessService
from app.core.services.auth.dto import UserJWTData
from app.core.services.auth.rbac import RBACManager
from app.core.websockets.base import BaseConnectionManager


@dataclass
class MockConnectionManager(BaseConnectionManager):
    bind_calls: list = field(default_factory=list)
    unbind_calls: list = field(default_factory=list)
    publish_calls: list = field(default_factory=list)
    publish_bulk_calls: list = field(default_factory=list)
    connections_map: dict = field(default_factory=dict)

    async def bind_key_connections(self, source_key: str, target_key: str) -> None:
        self.bind_calls.append({"source": source_key, "target": target_key})

    async def unbind_key_connections(self, source_key: str, target_key: str) -> None:
        self.unbind_calls.append({"source": source_key, "target": target_key})

    async def publish(self, key: str, payload: Any) -> None:
        self.publish_calls.append({"key": key, "payload": payload})

    async def publish_bulk(self, keys: list[str], payload: Any) -> None:
        self.publish_bulk_calls.append({"keys": keys, "payload": payload})

    async def accept_connection(self, websocket: Any, key: str) -> None:
        pass

    async def remove_connection(self, websocket: Any, key: str) -> None:
        pass

    async def bind_connection(self, websocket: Any, key: str) -> None:
        pass

    async def send_all(self, key: str, bytes_: bytes) -> None:
        pass

    async def send_json_all(self, key: str, data: dict[str, Any]) -> None:
        pass

    async def disconnect_all(self, key: str) -> None:
        pass

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass


@pytest_asyncio.fixture
async def chat_repository(db_session: AsyncSession, redis_client: Redis) -> ChatRepository:
    return ChatRepository(session=db_session, redis=redis_client)


@pytest_asyncio.fixture
async def message_repository(db_session: AsyncSession) -> MessageRepository:
    return MessageRepository(session=db_session)


@pytest_asyncio.fixture
async def read_receipt_repository(db_session: AsyncSession, redis_client: Redis) -> ReadReceiptRepository:
    return ReadReceiptRepository(session=db_session, redis=redis_client)


@pytest.fixture
def mock_connection_manager() -> BaseConnectionManager:
    return MockConnectionManager()


@pytest.fixture
def chat_access_service(rbac_manager: RBACManager) -> ChatAccessService:
    return ChatAccessService(rbac_manager=rbac_manager)


@pytest.fixture
def owner_jwt(make_user_jwt) -> UserJWTData:
    return make_user_jwt(id="10", username="owner")


@pytest.fixture
def member_jwt(make_user_jwt) -> UserJWTData:
    return make_user_jwt(id="20", username="member")


@pytest.fixture
def stranger_jwt(make_user_jwt) -> UserJWTData:
    return make_user_jwt(id="99", username="stranger")


@pytest_asyncio.fixture
async def persisted_group_chat(
    db_session: AsyncSession,
    owner_jwt: UserJWTData,
    member_jwt: UserJWTData
) -> Chat:
    chat = Chat.create(
        created_by=int(owner_jwt.id),
        members_ids=[int(member_jwt.id)],
        chat_type=ChatType.GROUP,
        name="Test Group",
        description="Test description",
        is_public=True,
    )
    db_session.add(chat)
    await db_session.commit()
    await db_session.refresh(chat)
    return chat


@pytest_asyncio.fixture
async def persisted_group_chat_with_member(
    db_session: AsyncSession,
    owner_jwt: UserJWTData,
    member_jwt: UserJWTData,
) -> Chat:
    chat = Chat.create(
        created_by=int(owner_jwt.id),
        members_ids=[int(member_jwt.id)],
        chat_type=ChatType.GROUP,
        name="Test Group With Members",
        description="desc",
        is_public=False,
    )
    db_session.add(chat)
    await db_session.flush()
    await db_session.refresh(chat)
    return chat


@pytest_asyncio.fixture
async def persisted_direct_chat(
    db_session: AsyncSession,
    owner_jwt: UserJWTData,
    member_jwt: UserJWTData,
) -> Chat:
    chat = Chat.create(
        created_by=int(owner_jwt.id),
        members_ids=[int(member_jwt.id)],
        chat_type=ChatType.DIRECT,
    )
    db_session.add(chat)
    await db_session.flush()
    await db_session.refresh(chat)
    return chat


@pytest_asyncio.fixture
async def persisted_message(
    db_session: AsyncSession,
    persisted_group_chat_with_member: Chat,
    owner_jwt: UserJWTData,
) -> Message:
    msg = Message.create(
        sender_id=int(owner_jwt.id),
        chat_id=persisted_group_chat_with_member.id,
        content="Hello world",
        message_type=MessageType.TEXT,
    )
    db_session.add(msg)
    await db_session.flush()
    await db_session.refresh(msg)
    return msg
