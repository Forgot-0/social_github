from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base_model import BaseModel, DateMixin


class ChatUserProfile(BaseModel, DateMixin):
    __tablename__ = "chat_user_profiles"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True, autoincrement=False)

    username: Mapped[str] = mapped_column(String, nullable=False)

    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_s3_keys: Mapped[dict] = mapped_column(JSONB, nullable=True, default="{}")

    @classmethod
    def create(
        cls, user_id: int, username: str,
        display_name: str | None=None,
        avatar_s3_key: dict | None = None,
    ) -> ChatUserProfile:
        instance = cls(
            user_id=user_id,
            username=username,
            display_name=display_name,
            avatar_s3_key=avatar_s3_key or {}
        )
        return instance

