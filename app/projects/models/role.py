from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel


class ProjectRole(BaseModel):

    __tablename__ = "project_roles"


    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    permissions: Mapped[dict] = mapped_column(JSONB, server_default="{}")


    def has_permission(self, permission_key: str) -> bool:
        return bool(self.permissions.get(permission_key))
