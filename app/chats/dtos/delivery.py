from collections.abc import Iterable, Iterator
from typing import Any

from app.chats.schemas.ws import WSEventType
from app.core.consumers.event import DictEventDTO

CHAT_DOMAIN_EVENT_PREFIX = "chats."

CHAT_EVENT_TO_WS_TYPE: dict[str, str] = {
    "chats.message.sent": WSEventType.NEW_MESSAGE.value,
    "chats.message.modified": WSEventType.MESSAGE_EDITED.value,
    "chats.message.deleted": WSEventType.MESSAGE_DELETED.value,
    "chats.message.readed": WSEventType.MESSAGES_READ.value,
    "chats.member.added": WSEventType.MEMBER_JOINED.value,
    "chats.member.left": WSEventType.MEMBER_LEFT.value,
    "chats.member.kicked": WSEventType.MEMBER_KICK.value,
    "chats.member.banned": WSEventType.MEMBER_BANNED.value,
    "chats.chat.created": WSEventType.CHAT_CREATED.value,
    "chats.chat.updated": WSEventType.CHAT_UPDATED.value,
    "chats.message.reaction_updated": WSEventType.REACTION_UPDATED.value,
}

_ENVELOPE_FIELDS = {
    "event_id",
    "event_name",
    "created_at",
}


def is_chat_domain_event(event_name: str) -> bool:
    return event_name.startswith(CHAT_DOMAIN_EVENT_PREFIX)


def build_ws_event(event: DictEventDTO) -> dict[str, Any]:
    chat_id = event.payload.get("chat_id")

    payload = {
        key: value
        for key, value in event.payload.items()
        if key not in _ENVELOPE_FIELDS and key != "chat_id"
    }

    ws_event: dict[str, Any] = {
        "type": CHAT_EVENT_TO_WS_TYPE.get(event.event_name, event.event_name),
        "event_name": event.event_name,
        "event_id": str(event.event_id),
        "chat_id": str(chat_id) if chat_id is not None else None,
        "payload": payload,
        "ts": str(event.payload.get("created_at") or ""),
    }

    if "seq" in event.payload:
        ws_event["seq"] = event.payload["seq"]

    return ws_event


def chunks(items: Iterable[int], size: int) -> Iterator[list[int]]:
    if size <= 0:
        raise ValueError("size must be greater than zero")

    batch: list[int] = []

    for item in items:
        batch.append(item)

        if len(batch) >= size:
            yield batch
            batch = []

    if batch:
        yield batch
