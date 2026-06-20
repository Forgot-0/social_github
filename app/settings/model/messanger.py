from typing import Self

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base_model import BaseModel, DateMixin
from app.settings.model.appearance import FontSize


class UserChatSettings(BaseModel, DateMixin):
    __tablename__ = "user_chat_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)

    enter_to_send: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Enter отправляет сообщение; если False — Shift+Enter",
    )

    link_previews: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Показывать превью ссылок в сообщениях",
    )
    message_font_size: Mapped[FontSize] = mapped_column(
        SAEnum(FontSize), nullable=False, default=FontSize.MEDIUM,
    )

    save_to_gallery: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Автосохранение входящих фото/видео в галерею",
    )

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
