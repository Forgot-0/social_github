from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base_model import BaseModel, DateMixin
from app.core.events.event import BaseEvent
from app.core.utils import now_utc

if TYPE_CHECKING:
    from app.chats.models.message import Message


@dataclass(frozen=True)
class SendedMessageEvent(BaseEvent):
    __event_name__ = "chat.messages.sended"
    chat_id: int
    message_id: int
    sender_id: int
    recipient_id: int
    text: str


class Chat(BaseModel, DateMixin):
    __tablename__ = "chats"
    __table_args__ = (
        UniqueConstraint("user_id_1", "user_id_2", name="uq_chat_users"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id_1: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id_2: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )

    @classmethod
    def canonical_pair(cls, a: int, b: int) -> tuple[int, int]:
        return (min(a, b), max(a, b))

    def send_message(self, sender_id: int, text: str, message_id: int) -> None:
        self.last_message_at = now_utc()
        self.register_event(
            SendedMessageEvent(
                chat_id=self.id,
                sender_id=sender_id,
                recipient_id=self.user_id_1 if sender_id != self.user_id_1 else self.user_id_2,
                text=text,
                message_id=message_id,
            )
        )

