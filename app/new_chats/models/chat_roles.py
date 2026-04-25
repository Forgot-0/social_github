from typing import Self

from sqlalchemy import JSON, BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel


class ChatRole(BaseModel):
    __tablename__ = "chat_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    name: Mapped[str] = mapped_column(
        String(32),
        nullable=False, index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1)
    permissions: Mapped[dict[str, bool]] = mapped_column(JSON, server_default="{}")

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
        if len(name) > 32:
            raise

