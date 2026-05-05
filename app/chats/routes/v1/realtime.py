from typing import Any

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from app.chats.dtos.members import MemberPresenceDTO
from app.chats.schemas.rest import PresenceBatchRequest
from app.chats.services.presence import PresenceService
from app.chats.services.ws import ChatConnectionManager
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter(route_class=DishkaRoute)


@router.post("/presence", response_model=list[MemberPresenceDTO])
async def get_presence_batch(
    payload: PresenceBatchRequest,
    _user_jwt_data: CurrentUserJWTData,
    presence_service: FromDishka[PresenceService],
) -> list[MemberPresenceDTO]:
    statuses = await presence_service.get_online_status(payload.user_ids)
    return [MemberPresenceDTO(user_id=user_id, is_online=statuses.get(user_id, False)) for user_id in payload.user_ids]


@router.get("/ws/status")
async def websocket_gateway_status(
    _user_jwt_data: CurrentUserJWTData,
    manager: FromDishka[ChatConnectionManager],
) -> dict[str, Any]:
    return {
        "gateway_id": manager.gateway_id,
        "stream_key": manager.stream_key,
        "connections": len(manager.connections_by_id),
        "users": len(manager.connections_by_user),
        "subscribed_chats": len(manager.subscriptions_by_chat),
    }
