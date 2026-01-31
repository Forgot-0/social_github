from typing import Self

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel
from app.projects.config import project_config


class ProjectRole(BaseModel):
    __tablename__ = "project_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    name: Mapped[str] = mapped_column(String(project_config.MAX_LEN_ROLE_NAME), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    permissions: Mapped[dict[str, bool]] = mapped_column(JSONB, server_default="{}")

    @classmethod
    def create(cls, name: str, level: int, permissions: dict[str, bool]) -> Self:
        instance = cls(
            name=name,
            level=level,
            permissions=permissions
        )
        instance._validate_role_name(name)
        return instance

    def has_permission(self, permission_key: str) -> bool:
        return bool(self.permissions.get(permission_key))

    def _validate_role_name(self, name: str) -> None:
        if len(name) > project_config.MAX_LEN_ROLE_NAME:
            raise

