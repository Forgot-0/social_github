import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaRouter

from app.chats.commands.profiles.upsert import UpsertProfileProjectionCommand
from app.chats.config import chat_config
from app.core.consumers.idempotency import EventIdempotencyGuard, extract_event_id
from app.core.mediators.base import BaseMediator

logger = logging.getLogger(__name__)

router = KafkaRouter()

PROFILE_EVENT_NAMES = frozenset({
    "profiles.profile.created",
    "profiles.profile.updated",
})


def parse_profile_event(event: dict[str, Any]) -> UpsertProfileProjectionCommand | None:
    event_name = str(event.get("event_name") or "")
    if event_name and event_name not in PROFILE_EVENT_NAMES:
        return None

    raw_user_id = event.get("user_id")
    if raw_user_id is None:
        return None

    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return None

    raw_username = event.get("username")
    username = str(raw_username) if raw_username is not None else None

    raw_event_id = event.get("event_id")
    event_id: UUID | None = None
    if raw_event_id:
        try:
            event_id = UUID(str(raw_event_id))
        except ValueError:
            event_id = None

    raw_created_at = event.get("created_at")
    event_updated_at: datetime | None = None
    if raw_created_at:
        try:
            event_updated_at = datetime.fromisoformat(str(raw_created_at))
        except ValueError:
            event_updated_at = None

    avatars = event.get("avatars")
    if not isinstance(avatars, dict):
        avatars = {}

    return UpsertProfileProjectionCommand(
        user_id=user_id,
        username=username,
        display_name=event.get("display_name"),
        avatars=avatars,
        event_id=event_id,
        event_updated_at=event_updated_at,
    )


@router.subscriber(
    chat_config.PROFILE_TOPIC,
    group_id=chat_config.PROFILE_PROJECTION_GROUP_ID,
)
@inject
async def route_profile_delivery_event(
    event: dict[str, Any],
    mediator: FromDishka[BaseMediator],
    idempotency_guard: FromDishka[EventIdempotencyGuard],
) -> None:
    command = parse_profile_event(event)
    if command is None:
        logger.debug(
            "Ignoring non-projection profile event",
            extra={"event_name": event.get("event_name"), "event_id": event.get("event_id")},
        )
        return

    event_id = extract_event_id(event)
    guard_group = chat_config.PROFILE_PROJECTION_GROUP_ID
    if event_id is not None and not await idempotency_guard.try_acquire(
        group=guard_group, event_id=event_id
    ):
        return

    try:
        await mediator.handle_command(command)
    except Exception:
        if event_id is not None:
            await idempotency_guard.release(group=guard_group, event_id=event_id)
        raise
