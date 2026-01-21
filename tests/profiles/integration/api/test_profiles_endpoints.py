from httpx import AsyncClient
import pytest


@pytest.mark.integration
@pytest.mark.profiles
class TestProfileEndpoints:

    @pytest.mark.asyncio
    async def test_create_endpoint(
        self,
        client: AsyncClient,
    ):
        ...