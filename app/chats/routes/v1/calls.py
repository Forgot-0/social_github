from __future__ import annotations

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status

from app.chats.commands.calls.join import JoinCallCommand, JoinCallCommandHandler
from app.chats.commands.calls.mute import MuteParticipantCommand, MuteParticipantCommandHandler
from app.chats.dtos.livekit import JoinTokenDTO
from app.chats.schemas.rest import MuteParticipantRequest
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter()


@router.post("/join", response_model=JoinTokenDTO)
@inject
async def join_call(
    chat_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[JoinCallCommandHandler],
) -> JoinTokenDTO:
    return await handler.handle(JoinCallCommand(user_jwt_data=user_jwt_data, chat_id=chat_id))


@router.post("/participants/{user_id}/mute", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def mute_participant(
    chat_id: UUID,
    user_id: int,
    payload: MuteParticipantRequest,
    user_jwt_data: CurrentUserJWTData,
    handler: FromDishka[MuteParticipantCommandHandler],
) -> None:
    await handler.handle(
        MuteParticipantCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
            muted=payload.muted,
        )
    )
