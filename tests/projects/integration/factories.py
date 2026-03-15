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


