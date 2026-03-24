from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class WSEventType(str, Enum):
    NEW_MESSAGE = "new_message"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_EDITED = "message_edited"
    MESSAGES_READ = "messages_read"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_KICK = "member_kick"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    PING = "ping"


class WSEvent(BaseModel):
    type: WSEventType
    chat_id: int
    payload: dict[str, Any] = {}
    ts: str = ""


class WSNewMessagePayload(BaseModel):
    id: int
    chat_id: int
    author_id: int
    content: str | None
    created_at: datetime
    is_edited: bool = False
    reply_to_id: int | None = None


class WSModifyMessagePayload(BaseModel):
    id: int
    chat_id: int
    author_id: int
    content: str | None


class WSMessagesReadPayload(BaseModel):
    chat_id: int
    user_id: int
    last_read_message_id: int


class WSTypingPayload(BaseModel):
    chat_id: int
    user_id: int


class WSClientEvent(BaseModel):
    type: WSEventType
    chat_id: int
    payload: dict[str, Any] = {}
