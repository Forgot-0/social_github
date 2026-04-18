from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.models.chat_roles import ChatRole
from app.core.db.base_model import BaseModel, DateMixin

if TYPE_CHECKING:
    from app.chats.models.chat import Chat



class ChatMember(BaseModel, DateMixin):
    __tablename__ = "chat_members"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_roles.id", ondelete="CASCADE"), index=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    is_muted:  Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    permissions_overrides: Mapped[dict[str, bool]] = mapped_column(JSONB, server_default="{}")

    chat: Mapped["Chat"] = relationship(back_populates="members", lazy="noload")
    role: Mapped["ChatRole"] = relationship("ChatRole")

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_chat_member"),
        Index("ix_chat_members_user_chat", "user_id", "chat_id"),
    )

    def effective_permissions(self) -> dict[str, bool]:
        perms = self.role.permissions.copy() if self.role is not None else {}
        if self.permissions_overrides:
            perms.update(self.permissions_overrides)
        return perms

    def has_permission(self, permission_key: str) -> bool:
        if self.role is None:
            return False
        if self.permissions_overrides and permission_key in self.permissions_overrides:
            return bool(self.permissions_overrides[permission_key])
        return self.role.has_permission(permission_key)

    @property
    def role_name(self) -> str | None:
        return self.role.name if self.role is not None else None

