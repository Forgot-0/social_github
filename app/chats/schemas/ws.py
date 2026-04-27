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
    chat_id: str
    payload: dict[str, Any] = {}
    ts: str = ""


class AttachmentSuccessPayload(BaseModel):
    user_id: int
    chat_id: str
    tokens: list[str]

