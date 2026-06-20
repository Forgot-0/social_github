# ruff: noqa: F401
from enum import Enum as PyEnum
from typing import Self
from datetime import time

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin


class TwoFactorMethod(str, PyEnum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"


class AppTheme(str, PyEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class DateFormat(str, PyEnum):
    DMY = "dmy"
    MDY = "mdy"
    YMD = "ymd"


class TimeFormat(str, PyEnum):
    H12 = "12h"
    H24 = "24h"


class FontSize(str, PyEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class MessageDensity(str, PyEnum):
    COMPACT = "compact"
    NORMAL = "normal"
    COMFORTABLE = "comfortable"


class BlockReason(str, PyEnum):
    PERSONAL = "personal"
    SPAM = "spam"
    ABUSE = "abuse"
    OTHER = "other"


# ---------------------------------------------------------------------------
# 1. UserPrivacySettings
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# 2. UserNotificationSettings
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 3. UserSecuritySettings
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# 4. UserAppearanceSettings
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# 5. UserChatSettings
# ---------------------------------------------------------------------------


class UserChatSettings(BaseModel, DateMixin):
    """
    Персональные настройки мессенджера.
    Не путать с настройками конкретного чата (ChatMember/Chat).
    """

    __tablename__ = "user_chat_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)

    # --- Ввод ---
    enter_to_send: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Enter отправляет сообщение; если False — Shift+Enter",
    )

    # --- Отображение ---
    link_previews: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Показывать превью ссылок в сообщениях",
    )
    message_font_size: Mapped[FontSize] = mapped_column(
        SAEnum(FontSize), nullable=False, default=FontSize.MEDIUM,
    )

    # --- Медиа в чате ---
    save_to_gallery: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Автосохранение входящих фото/видео в галерею",
    )

    # --- Архив и фильтры ---
    show_archived_chats: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Показывать архивированные чаты в общем списке",
    )
    filter_unknown_senders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Скрывать сообщения от незнакомцев в отдельную папку",
    )

    @classmethod
    def create_default(cls, user_id: int) -> Self:
        return cls(user_id=user_id)

    __table_args__ = (
        Index("ix_chat_settings_user_id", "user_id"),
    )


# ---------------------------------------------------------------------------
# 6. BlockedUser
# ---------------------------------------------------------------------------


class BlockedUser(BaseModel, DateMixin):
    """
    Список заблокированных пользователей.
    Блокировка двусторонняя по логике: A блокирует B →
    ни A не пишет B, ни B не пишет A, профили скрыты друг от друга.
    Проверяется в chats и profiles сервисах через Redis-кеш.
    """

    __tablename__ = "blocked_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    blocker_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Кто заблокировал",
    )
    blocked_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Кого заблокировали",
    )
    reason: Mapped[BlockReason | None] = mapped_column(
        SAEnum(BlockReason), nullable=True,
    )
    note: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
        comment="Личная заметка пользователя о причине блокировки",
    )

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_blocked_users"),
        Index("ix_blocked_users_blocker", "blocker_id"),
        Index("ix_blocked_users_blocked", "blocked_id"),
    )


# ---------------------------------------------------------------------------
# 7. MutedUser
# ---------------------------------------------------------------------------


class MutedUser(BaseModel, DateMixin):
    """
    Заглушенные пользователи.
    В отличие от блокировки — мягкое действие:
    заглушенный может писать и видеть профиль,
    пользователь просто не получает уведомлений от него.
    """

    __tablename__ = "muted_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Кто заглушил",
    )
    muted_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Кого заглушили",
    )
    muted_until: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True,
        comment="Unix timestamp до которого заглушён; null = навсегда",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "muted_id", name="uq_muted_users"),
        Index("ix_muted_users_user", "user_id"),
        Index("ix_muted_users_muted", "muted_id"),
    )


# ---------------------------------------------------------------------------
# 8. UserDeviceToken — токены устройств для push-уведомлений
# ---------------------------------------------------------------------------


class UserDeviceToken(BaseModel, DateMixin):
    __tablename__ = "user_device_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    token: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="FCM registration token или APNs device token",
    )
    platform: Mapped[str] = mapped_column(
        String(16), nullable=False,
        comment="android | ios | web",
    )
    device_name: Mapped[str | None] = mapped_column(
        String(128), nullable=True,
        comment="Читаемое имя: 'iPhone 15 Pro', 'Chrome on Windows'",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("user_id", "token", name="uq_device_token"),
        Index("ix_device_tokens_user_active", "user_id", "is_active"),
    )
