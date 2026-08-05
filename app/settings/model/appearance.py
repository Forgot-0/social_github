from enum import StrEnum
from typing import Self

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum as SAEnum,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin


class AppTheme(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class DateFormat(StrEnum):
    DMY = "dmy"
    MDY = "mdy"
    YMD = "ymd"


class TimeFormat(StrEnum):
    H12 = "12h"
    H24 = "24h"


class FontSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class MessageDensity(StrEnum):
    COMPACT = "compact"
    NORMAL = "normal"
    COMFORTABLE = "comfortable"



class UserAppearanceSettings(BaseModel, DateMixin):
    __tablename__ = "user_appearance_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)

    theme: Mapped[AppTheme] = mapped_column(
        SAEnum(AppTheme), nullable=False, default=AppTheme.SYSTEM,
    )
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en",
        comment="ISO 639-1 код языка, например 'en', 'ru'",
    )
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="UTC",
        comment="IANA timezone, например 'Europe/Moscow'",
    )
    date_format: Mapped[DateFormat] = mapped_column(
        SAEnum(DateFormat), nullable=False, default=DateFormat.DMY,
    )
    time_format: Mapped[TimeFormat] = mapped_column(
        SAEnum(TimeFormat), nullable=False, default=TimeFormat.H24,
    )

    font_size: Mapped[FontSize] = mapped_column(
        SAEnum(FontSize), nullable=False, default=FontSize.MEDIUM,
    )
    message_density: Mapped[MessageDensity] = mapped_column(
        SAEnum(MessageDensity), nullable=False, default=MessageDensity.NORMAL,
    )

    autoplay_video: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    autoplay_gif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    auto_download_photos_mobile: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_download_photos_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_download_video_mobile: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Видео по мобильной сети не грузим по умолчанию",
    )
    auto_download_video_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_download_files_mobile: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_download_files_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    @classmethod
    def create_default(cls, user_id: int) -> Self:
        return cls(user_id=user_id)

