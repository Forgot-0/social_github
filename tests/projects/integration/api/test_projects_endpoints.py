from httpx import AsyncClient
import pytest

from app.core.services.auth.dto import UserJWTData


@pytest.mark.integration
@pytest.mark.projects
class TestProjectEndpoints:
    @pytest.mark.asyncio
    async def test_create_project_endpoint(
        self,
        client: AsyncClient,
        user_jwt: UserJWTData,
        create_auth_headers
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.post(
            "/api/v1/projects/",
            json={
                "name": "Endpoint project",
                "slug": "endpoint-project",
                "description": "desc",
                "visibility": "public",
                "meta_data": {},
                "tags": [],
            },
            headers=headers
        )

        assert response.status_code == 201

