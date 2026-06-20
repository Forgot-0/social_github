from enum import Enum as PyEnum
from typing import Self

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum as SAEnum,
    SmallInteger,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin



class TwoFactorMethod(str, PyEnum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"


class UserSecuritySettings(BaseModel, DateMixin):
    __tablename__ = "user_security_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)

    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    two_factor_method: Mapped[TwoFactorMethod | None] = mapped_column(
        SAEnum(TwoFactorMethod), nullable=True,
        comment="Активный метод 2FA, null если 2FA выключена",
    )

    notify_on_new_login: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Email/push при входе с нового устройства",
    )
    notify_on_password_change: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_on_email_change: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    login_activity_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Показывать ли историю входов другим (например, доверенным лицам)",
    )

    remember_trusted_devices: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    trusted_device_duration_days: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=30,
        comment="Сколько дней устройство считается доверенным",
    )

    @classmethod
    def create(cls, user_id: int) -> Self:
        return cls(user_id=user_id)
