import pytest
from httpx import AsyncClient

from app.core.services.auth.dto import UserJWTData
from app.projects.models.application import Application
from app.projects.models.position import Position
from app.projects.models.project import Project


@pytest.mark.integration
@pytest.mark.projects
class TestProjectEndpoints:

    @pytest.mark.asyncio
    async def test_create_project_success(
        self,
        client: AsyncClient,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.post(
            "/api/v1/projects/",
            json={
                "name": "API Test Project",
                "slug": "api-test-project",
                "description": "desc",
                "visibility": "public",
                "meta_data": {},
                "tags": ["python"],
            },
            headers=headers,
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_project_unauthorized(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            "/api/v1/projects/",
            json={"name": "Test", "slug": "test"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_project_success(
        self,
        client: AsyncClient,
        persisted_project: Project,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.get(
            f"/api/v1/projects/{persisted_project.id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == persisted_project.id
        assert data["owner_id"] == persisted_project.owner_id

    @pytest.mark.asyncio
    async def test_get_project_not_found(
        self,
        client: AsyncClient,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.get("/api/v1/projects/999999", headers=headers)

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND_PROJECT"

    @pytest.mark.asyncio
    async def test_update_project_success(
        self,
        client: AsyncClient,
        persisted_project: Project,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.put(
            f"/api/v1/projects/{persisted_project.id}",
            json={"name": "Updated via API"},
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_project_not_owner_forbidden(
        self,
        client: AsyncClient,
        persisted_project: Project,
        make_user_jwt,
        create_auth_headers,
    ) -> None:
        stranger_jwt = make_user_jwt(id="999", username="stranger")
        headers = create_auth_headers(stranger_jwt)

        response = await client.put(
            f"/api/v1/projects/{persisted_project.id}",
            json={"name": "Hijacked"},
            headers=headers,
        )

        assert response.status_code in (403, 422, 500)

    @pytest.mark.asyncio
    async def test_invite_member_success(
        self,
        client: AsyncClient,
        persisted_project: Project,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.post(
            f"/api/v1/projects/{persisted_project.id}/invite",
            json={"user_id": 800, "role_id": 5},
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_accept_invite_not_member_returns_error(
        self,
        client: AsyncClient,
        persisted_project: Project,
        make_user_jwt,
        create_auth_headers,
    ) -> None:
        stranger_jwt = make_user_jwt(id="901", username="notinvited")
        headers = create_auth_headers(stranger_jwt)

        response = await client.post(
            f"/api/v1/projects/{persisted_project.id}/members/accept",
            headers=headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_position_for_project_success(
        self,
        client: AsyncClient,
        persisted_project: Project,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.post(
            f"/api/v1/projects/{persisted_project.id}/positions",
            json={
                "title": "Frontend Dev",
                "description": "We need a frontend developer",
                "required_skills": ["react", "typescript"],
            },
            headers=headers,
        )

        assert response.status_code == 201


@pytest.mark.integration
@pytest.mark.projects
class TestPositionEndpoints:

    @pytest.mark.asyncio
    async def test_list_positions_success(
        self,
        client: AsyncClient,
        persisted_position: Position,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.get(
            "/api/v1/positions/",
            params={"project_id": persisted_position.project_id},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_position_by_id_success(
        self,
        client: AsyncClient,
        persisted_position: Position,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.get(
            f"/api/v1/positions/{persisted_position.id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(persisted_position.id)
        assert data["title"] == persisted_position.title

    @pytest.mark.asyncio
    async def test_get_position_not_found(
        self,
        client: AsyncClient,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        from uuid import uuid4

        headers = create_auth_headers(user_jwt)

        response = await client.get(
            f"/api/v1/positions/{uuid4()}",
            headers=headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_position_success(
        self,
        client: AsyncClient,
        persisted_position: Position,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.put(
            f"/api/v1/positions/{persisted_position.id}",
            json={"title": "Updated Position Title"},
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_position_success(
        self,
        client: AsyncClient,
        persisted_position: Position,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.delete(
            f"/api/v1/positions/{persisted_position.id}",
            headers=headers,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_apply_to_position_success(
        self,
        client: AsyncClient,
        persisted_position: Position,
        make_user_jwt,
        create_auth_headers,
    ) -> None:
        candidate_jwt = make_user_jwt(id="850", username="applicant")
        headers = create_auth_headers(candidate_jwt)

        response = await client.post(
            f"/api/v1/positions/{persisted_position.id}/apply",
            json={"message": "I want to join this project"},
            headers=headers,
        )

        assert response.status_code == 201


@pytest.mark.integration
@pytest.mark.projects
class TestApplicationEndpoints:

    @pytest.mark.asyncio
    async def test_list_applications_success(
        self,
        client: AsyncClient,
        persisted_application: Application,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.get(
            "/api/v1/applications/",
            params={
                "project_id": persisted_application.project_id,
                "status": "pending",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        ids = [a["id"] for a in data["items"]]
        assert str(persisted_application.id) in ids

    @pytest.mark.asyncio
    async def test_approve_application_success(
        self,
        client: AsyncClient,
        persisted_application: Application,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.post(
            f"/api/v1/applications/{persisted_application.id}/approve",
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_reject_application_success(
        self,
        client: AsyncClient,
        persisted_application: Application,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.post(
            f"/api/v1/applications/{persisted_application.id}/reject",
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_applications_filter_by_candidate(
        self,
        client: AsyncClient,
        persisted_application: Application,
        user_jwt: UserJWTData,
        create_auth_headers,
    ) -> None:
        headers = create_auth_headers(user_jwt)

        response = await client.get(
            "/api/v1/applications/",
            params={
                "candidate_id": persisted_application.candidate_id,
                "status": "pending",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        ids = [a["id"] for a in data["items"]]
        assert str(persisted_application.id) in ids
