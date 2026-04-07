import logging

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.chats.exceptions import LiveKitServiceException
from app.chats.keys import ChatKeys
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.message import MessageRepository
from app.chats.schemas.ws import WSEventType
from app.chats.services.livekit_service import LiveKitService
from app.chats.services.system_message import SystemMessageService
from app.core.events.service import BaseEventBus
from app.core.utils import now_utc
from app.core.websockets.base import BaseConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(route_class=DishkaRoute)

_EV_ROOM_STARTED = "room_started"
_EV_ROOM_FINISHED = "room_finished"
_EV_PARTICIPANT_JOINED = "participant_joined"
_EV_PARTICIPANT_LEFT = "participant_left"


@router.post(
    "/livekit/webhook",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def livekit_webhook(
    request: Request,
    livekit_service: FromDishka[LiveKitService],
    chat_repository: FromDishka[ChatRepository],
    message_repository: FromDishka[MessageRepository],
    session: FromDishka[AsyncSession],
    connection_manager: FromDishka[BaseConnectionManager],
    event_bus: FromDishka[BaseEventBus],
) -> dict:
    raw_body = await request.body()
    auth_header = request.headers.get("Authorization", "")

    try:
        event = livekit_service.receive_webhook(raw_body.decode(), auth_header)
    except LiveKitServiceException as exc:
        logger.warning("Rejected LiveKit webhook: %s", exc.detail)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    event_type = event.event
    room_slug = event.room.name
    chat_id = int(room_slug.split(":")[-1])

    logger.debug("LiveKit webhook received", extra={"event": event_type, "slug": room_slug})

    if not room_slug:
        return {"ok": True}

    svc = SystemMessageService(
        session=session,
        message_repository=message_repository,
        chat_repository=chat_repository,
        event_bus=event_bus,
    )
    identity = event.participant.identity if event.participant else ""
    participant_name = event.participant.name if event.participant else identity

    if event_type == _EV_ROOM_STARTED:

        await svc.send(
            chat_id=chat_id,
            content=f"📞 {participant_name} started a call",
        )
        await connection_manager.publish(
            ChatKeys.chat_channel(chat_id),
            {
                "type": WSEventType.CALL_STARTED,
                "chat_id": chat_id,
                "payload": {
                    "slug": room_slug,
                    "started_by": identity,
                    "username": participant_name,
                },
            },
        )

    elif event_type == _EV_PARTICIPANT_JOINED:
        await svc.send(
            chat_id=chat_id,
            content=f"📞 {participant_name} joined the call",
        )
        await connection_manager.publish(
            ChatKeys.chat_channel(chat_id),
            {
                "type": WSEventType.CALL_JOINED,
                "chat_id": chat_id,
                "payload": {
                    "user_id": int(identity) if identity.isdigit() else None,
                    "username": participant_name,
                },
            },
        )

    elif event_type == _EV_PARTICIPANT_LEFT:
        await svc.send(
            chat_id=chat_id,
            content=f"📴 {participant_name} left the call",
        )
        await connection_manager.publish(
            ChatKeys.chat_channel(chat_id),
            {
                "type": WSEventType.CALL_LEFT,
                "chat_id": chat_id,
                "payload": {
                    "user_id": int(identity) if identity.isdigit() else None,
                    "username": participant_name,
                },
            },
        )

    elif event_type == _EV_ROOM_FINISHED:
        duration = now_utc().timestamp() - event.room.creation_time
        mins, secs = divmod(duration, 60)
        duration_str = f"{mins}:{secs:02d}"

        await svc.send(
            chat_id=chat_id,
            content=f"📵 Call ended (duration: {duration_str})",
        )
        await connection_manager.publish(
            ChatKeys.chat_channel(chat_id),
            {
                "type": WSEventType.CALL_ENDED,
                "chat_id": chat_id,
                "payload": {
                    "duration_seconds": duration
                },
            },
        )

        logger.info(
            "Call ended via webhook",
            extra={"chat_id": chat_id, "slug": room_slug, "duration": duration},
        )

    return {"ok": True}
