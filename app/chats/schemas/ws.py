from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WSEventType(str, Enum):
    NEW_MESSAGE = "new_message"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_EDITED = "message_edited"
    MESSAGES_READ = "messages_read"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_KICK = "member_kick"
    MEMBER_BANNED = "member_banned"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    PING = "ping"

    ATTACHMENT_SUCCESS = "attachment_success"

    CHAT_CREATED = "chat_created"
    CHAT_UPDATED = "chat_updated"

    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    CALL_JOINED = "call_joined"
    CALL_LEFT = "call_left"


class WSClientOp(str, Enum):
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    RESUME = "resume"


class WSEvent(BaseModel):
    type: WSEventType | str
    chat_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    ts: str = ""


class WSClientCommand(BaseModel):
    op: WSClientOp
    chat_id: str | None = None
    last_seq: int | None = None
    cursors: dict[str, int] = Field(default_factory=dict)


class WSReadyPayload(BaseModel):
    connection_id: str
    gateway_id: str
    heartbeat_interval: int
    heartbeat_timeout: int


class AttachmentSuccessPayload(BaseModel):
    user_id: int
    chat_id: str
    tokens: list[str]
