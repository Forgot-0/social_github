from httpx import AsyncClient
import pytest


@pytest.mark.integration
@pytest.mark.profiles
@pytest.mark.asyncio
class TestProfileEndpoints:

    async def test_create_endpoint(
        self,
        client: AsyncClient,
    ):
        ...