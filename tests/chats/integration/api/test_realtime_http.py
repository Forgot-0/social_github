import pytest
from httpx import AsyncClient

from app.chats.keys import ChatKeys
from app.core.services.auth.dto import UserJWTData
from app.core.utils import now_utc
from tests.support.http import api_path


@pytest.mark.integration
@pytest.mark.chats
@pytest.mark.asyncio
class TestRealtimeHttpEndpoints:
    async def test_presence_batch_unauthorized(self, client: AsyncClient) -> None:
        response = await client.post(
            api_path("chats/realtime/presence"),
            json={"user_ids": [1, 2]},
        )
        assert response.status_code == 403

    async def test_presence_batch_reflects_redis_scores(
        self,
        client: AsyncClient,
        user_jwt: UserJWTData,
        create_auth_headers,
        redis_client,
    ) -> None:
        headers = create_auth_headers(user_jwt)
        online_uid = 60_001
        await redis_client.zadd(
            ChatKeys.presence_last_seen_zset(),
            {str(online_uid): now_utc().timestamp()},
        )

        response = await client.post(
            api_path("chats/realtime/presence"),
            json={"user_ids": [online_uid, 60_002]},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        by_user = {row["user_id"]: row["is_online"] for row in body}
        assert by_user[online_uid] is True
        assert by_user[60_002] is False

    async def test_ws_gateway_status_shape(
        self,
        client: AsyncClient,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        response = await client.get(
            api_path("chats/realtime/ws/status"),
            headers=create_auth_headers(user_jwt),
        )
        assert response.status_code == 200
        data = response.json()
        assert "gateway_id" in data
        assert "stream_key" in data
        assert "connections" in data
        assert "users" in data
        assert "subscribed_chats" in data
        assert isinstance(data["connections"], int)
