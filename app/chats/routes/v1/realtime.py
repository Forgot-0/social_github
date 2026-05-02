from __future__ import annotations

from typing import Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from app.chats.dtos.members import MemberPresenceDTO
from app.chats.schemas.rest import PresenceBatchRequest
from app.chats.services.presence import PresenceService
from app.core.services.auth.depends import CurrentUserJWTData
from app.core.websockets.base import BaseConnectionManager

router = APIRouter()


@router.post("/presence", response_model=list[MemberPresenceDTO])
@inject
async def get_presence_batch(
    payload: PresenceBatchRequest,
    _user_jwt_data: CurrentUserJWTData,
    presence_service: FromDishka[PresenceService],
) -> list[MemberPresenceDTO]:
    statuses = await presence_service.get_online_status(payload.user_ids)
    return [MemberPresenceDTO(user_id=user_id, is_online=statuses.get(user_id, False)) for user_id in payload.user_ids]


@router.get("/ws/status")
@inject
async def websocket_gateway_status(
    _user_jwt_data: CurrentUserJWTData,
    manager: FromDishka[BaseConnectionManager],
) -> dict[str, Any]:
    return {
        "gateway_id": getattr(manager, "gateway_id", "unknown"),
        "stream_key": getattr(manager, "stream_key", None),
        "connections": len(getattr(manager, "connections_by_id", {})),
        "users": len(getattr(manager, "connections_by_user", {})),
        "subscribed_chats": len(getattr(manager, "subscriptions_by_chat", {})),
    }
