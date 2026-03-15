from typing import Any


class ProjectCommandFactory:
    @staticmethod
    def create_command(
        owner_id: int,
        name: str,
        slug: str,
        small_description: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
        meta_data: dict[str, Any] | None = None,
        tags: set[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "owner_id": owner_id,
            "name": name,
            "slug": slug,
            "small_description": small_description,
            "description": description,
            "visibility": visibility,
            "meta_data": meta_data,
            "tags": tags,
        }

    @staticmethod
    def update_command(
        name: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
        meta_data: dict[str, Any] | None = None,
        tags: set[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "name": name,
            "description": description,
            "visibility": visibility,
            "meta_data": meta_data,
            "tags": tags,
        }


class PositionCommandFactory:
    @staticmethod
    def create_command(
        project_id: int,
        title: str = "Backend Developer",
        description: str = "We need help",
        required_skills: set[str] | None = None,
        responsibilities: str | None = None,
        location_type: str | None = None,
        expected_load: str | None = None,
    ) -> dict[str, Any]:
        return {
            "project_id": project_id,
            "title": title,
            "description": description,
            "required_skills": required_skills or {"python"},
            "responsibilities": responsibilities,
            "location_type": location_type,
            "expected_load": expected_load,
        }

    @staticmethod
    def update_command(
        title: str | None = None,
        description: str | None = None,
        responsibilities: str | None = None,
        required_skills: set[str] | None = None,
        location_type: str | None = None,
        expected_load: str | None = None,
    ) -> dict[str, Any]:
        return {
            "title": title,
            "description": description,
            "responsibilities": responsibilities,
            "required_skills": required_skills,
            "location_type": location_type,
            "expected_load": expected_load,
        }
