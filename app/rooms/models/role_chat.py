from typing import Self

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel, DateMixin


class RoomRole(BaseModel, DateMixin):
    __tablename__ = "room_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    permissions: Mapped[dict[str, bool]] = mapped_column(JSONB, server_default="{}")

    @classmethod
    def create(cls, name: str, level: int, permissions: dict[str, bool]) -> Self:
        if len(name) > 32:
            raise ValueError(f"Role name too long: {name}")
        return cls(name=name, level=level, permissions=permissions)

    def has_permission(self, permission_key: str) -> bool:
        return bool(self.permissions.get(permission_key))

    def update_permissions(self, permissions: dict[str, bool]) -> None:
        self.permissions = {**self.permissions, **permissions}
