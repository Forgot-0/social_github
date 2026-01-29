from typing import Self
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel
from app.projects.config import project_config


class ProjectRole(BaseModel):
    __tablename__ = "project_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    name: Mapped[str] = mapped_column(String(project_config.MAX_LEN_ROLE_NAME), nullable=False)
    permissions: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    @classmethod
    def create(cls, name: str, permissions: dict[str, bool]) -> Self:
        instance = cls(
            name=name,
            permissions=permissions
        )
        return instance

    def has_permission(self, permission_key: str) -> bool:
        return bool(self.permissions.get(permission_key))


    def _validate_role_name(self, name: str):
        if len(name) > project_config.MAX_LEN_ROLE_NAME:
            raise
