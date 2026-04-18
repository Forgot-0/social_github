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

    ATTACHMENT_SUCCESS = "attachment_success"

    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    CALL_JOINED = "call_joined"
    CALL_LEFT = "call_left"


class WSEvent(BaseModel):
    type: WSEventType
    chat_id: int
    payload: dict[str, Any] = {}
    ts: str = ""


class WSNewMessagePayload(BaseModel):
    id: int
    chat_id: int
    author_id: int | None
    content: str | None
    created_at: datetime
    is_edited: bool = False
    reply_to_id: int | None = None
    attachment_count: int = 0
    forwarded_from_chat_id: int | None = None
    forwarded_from_message_id: int | None = None


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


class WSCallPayload(BaseModel):
    chat_id: int
    slug: str | None = None
    started_by: int | None = None
    ended_by: int | None = None
    user_id: int | None = None
    username: str | None = None
    duration_seconds: int | None = None

class AttachmentSuccessPayload(BaseModel):
    user_id: int
    tokens: list[str]

