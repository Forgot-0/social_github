from enum import Enum as PyEnum
from typing import Self

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin


class VisibilityLevelEnum(str, PyEnum):
    EVERYONE = "everyone"
    CONTACTS = "contacts"
    NOBODY = "nobody"



class UserPrivacySettings(BaseModel, DateMixin):
    __tablename__ = "user_privacy_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)

    profile_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
        comment="Кто видит профиль целиком",
    )
    avatar_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
    )
    bio_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
    )
    birthday_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.CONTACTS,
    )
    phone_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.NOBODY,
        comment="Кто видит номер телефона",
    )

    last_seen_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
        comment="Кто видит время последнего визита",
    )
    online_status_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
        comment="Кто видит метку онлайн",
    )

    followers_list_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
    )
    following_list_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
    )
    friends_list_visibility: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.CONTACTS,
    )

    who_can_message: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
        comment="Кто может начать переписку",
    )
    who_can_add_to_groups: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.CONTACTS,
    )
    who_can_add_to_channels: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.CONTACTS,
    )
    show_read_receipts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Показывать ли галочки прочтения",
    )
    show_typing_indicator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Показывать ли индикатор печати",
    )

    searchable_by_username: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    searchable_by_phone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    searchable_by_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    appear_in_recommendations: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Появляться ли в разделе 'Люди, которых вы знаете'",
    )
    appear_in_nearby: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Появляться ли в поиске рядом",
    )

    who_can_comment: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
    )
    who_can_tag: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.CONTACTS,
        comment="Кто может отмечать пользователя на фото/постах",
    )
    who_can_share_posts: Mapped[VisibilityLevelEnum] = mapped_column(
        SAEnum(VisibilityLevelEnum), nullable=False, default=VisibilityLevelEnum.EVERYONE,
    )

    @classmethod
    def create(cls, user_id: int) -> Self:
        return cls(user_id=user_id)
