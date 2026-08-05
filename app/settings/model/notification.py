from datetime import time
from typing import Self

from sqlalchemy import (
    BigInteger,
    Boolean,
    String,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin


class UserNotificationSettings(BaseModel, DateMixin):
    __tablename__ = "user_notification_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)

    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    push_messages: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_group_messages: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_channel_messages: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_mentions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_replies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_reactions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    push_new_follower: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_new_comment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_post_like: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Лайки обычно не нужны в push — шумно",
    )
    push_friend_request: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_friend_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_birthday_reminder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_messages: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Дайджест непрочитанных сообщений на почту",
    )
    email_new_follower: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_security_alerts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Нельзя отключить полностью — безопасность",
    )
    email_product_updates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_marketing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    inapp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    inapp_messages: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    inapp_mentions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    inapp_reactions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    inapp_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quiet_hours_start: Mapped[time | None] = mapped_column(
        Time, nullable=True,
        comment="Начало тихого режима, например 23:00",
    )
    quiet_hours_end: Mapped[time | None] = mapped_column(
        Time, nullable=True,
        comment="Конец тихого режима, например 08:00",
    )
    quiet_hours_timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="UTC",
    )

    @classmethod
    def create(cls, user_id: int) -> Self:
        return cls(user_id=user_id)
