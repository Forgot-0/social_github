from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Path, Query, status

from app.chats.commands.reactions.remove import RemoveReactionCommand
from app.chats.commands.reactions.set import SetReactionCommand
from app.chats.config import chat_config
from app.chats.dtos.reactions import MessageReactionsDTO
from app.chats.queries.reactions.get_list import GetMessageReactionsQuery
from app.core.api.rate_limiter import ConfigurableRateLimiter
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter(route_class=DishkaRoute)

reaction_write_limiter = ConfigurableRateLimiter(
    times=chat_config.RATE_LIMIT_REACTIONS_PER_SECOND,
    seconds=1,
)

EmojiPath = Annotated[str, Path(min_length=1, max_length=32)]


@router.put(
    "/{emoji}/",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(reaction_write_limiter)],
)
async def set_reaction(
    chat_id: UUID,
    message_id: UUID,
    emoji: EmojiPath,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(
        SetReactionCommand(
            chat_id=chat_id,
            message_id=message_id,
            emoji=emoji,
            user_jwt_data=user_jwt_data,
        )
    )


@router.delete(
    "/{emoji}/",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(reaction_write_limiter)],
)
async def remove_reaction(
    chat_id: UUID,
    message_id: UUID,
    emoji: EmojiPath,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
) -> None:
    await mediator.handle_command(
        RemoveReactionCommand(
            chat_id=chat_id,
            message_id=message_id,
            emoji=emoji,
            user_jwt_data=user_jwt_data,
        )
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def get_message_reactions(
    chat_id: UUID,
    message_id: UUID,
    user_jwt_data: CurrentUserJWTData,
    mediator: FromDishka[BaseMediator],
    emoji: Annotated[str | None, Query(min_length=1, max_length=32)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor_user_id: Annotated[int | None, Query(ge=1)] = None,
) -> MessageReactionsDTO:
    return await mediator.handle_query(
        GetMessageReactionsQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
            emoji=emoji,
            limit=limit,
            cursor_user_id=cursor_user_id,
        )
    )
