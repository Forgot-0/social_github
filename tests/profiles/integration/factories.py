
from typing import Any
from uuid import uuid4


class ProfileCommandFactory:
    @staticmethod
    def create_command(
        user_id: int,
        username: str,
        display_name: str | None = None,
        bio: str | None = None,
        skills: set[str] | None = None
    ) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "bio": bio,
            "skills": skills,
        }

    @staticmethod
    def update_command(
        display_name: str | None = None,
        bio: str | None = None,
        skills: set[str] | None = None
    ) -> dict[str, Any]:
        return {
            "display_name": display_name,
            "bio": bio,
            "skills": skills,
        }

