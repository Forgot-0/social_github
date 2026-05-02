from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from app.chats.schemas.ws import WSEventType

CHAT_DOMAIN_EVENT_PREFIX = "chats."

CHAT_EVENT_TO_WS_TYPE: dict[str, str] = {
    "chats.message.sent": WSEventType.NEW_MESSAGE.value,
    "chats.message.modified": WSEventType.MESSAGE_EDITED.value,
    "chats.message.deleted": WSEventType.MESSAGE_DELETED.value,
    "chats.message.readed": WSEventType.MESSAGES_READ.value,
    "chats.member.added": WSEventType.MEMBER_JOINED.value,
    "chats.member.left": WSEventType.MEMBER_LEFT.value,
    "chats.member.kicked": WSEventType.MEMBER_KICK.value,
    "chats.member.banned": WSEventType.MEMBER_BANNED,
    "chats.chat.created": WSEventType.CHAT_CREATED,
    "chats.chat.updated": WSEventType.CHAT_UPDATED,
}

_ENVELOPE_FIELDS = {"event_id", "event_name", "created_at"}


def is_chat_domain_event(event: dict[str, Any]) -> bool:
    event_name = str(event.get("event_name") or "")
    return event_name.startswith(CHAT_DOMAIN_EVENT_PREFIX)


def build_ws_event(event: dict[str, Any]) -> dict[str, Any]:
    """Convert a durable Kafka domain event into a compact websocket event.

    The Kafka event is intentionally kept as the source of truth. The websocket
    payload includes the remaining event fields so clients can update optimistic
    state immediately and still use `last_seq` replay for loss recovery.
    """
    event_name = str(event.get("event_name") or "chat.event")
    chat_id = event.get("chat_id")
    payload = {
        key: value
        for key, value in event.items()
        if key not in _ENVELOPE_FIELDS and key != "chat_id"
    }

    ws_event: dict[str, Any] = {
        "type": CHAT_EVENT_TO_WS_TYPE.get(event_name, event_name),
        "event_name": event_name,
        "event_id": str(event.get("event_id") or ""),
        "chat_id": str(chat_id) if chat_id is not None else None,
        "payload": payload,
        "ts": str(event.get("created_at") or ""),
    }
    if "seq" in event:
        ws_event["seq"] = event["seq"]
    return ws_event


def chunks(items: Iterable[int], size: int) -> Iterator[list[int]]:
    batch: list[int] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch
