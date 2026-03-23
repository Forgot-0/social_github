from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.chats.commands.chats.add_member import AddMemberCommand
from app.chats.commands.chats.ban_member import BanMemberCommand
from app.chats.commands.chats.change_role import ChangeMemberRoleCommand
from app.chats.commands.chats.create import CreateChatCommand

from app.chats.commands.chats.kick_member import KickMemberCommand
from app.chats.commands.chats.leave import LeaveChatCommand
from app.chats.commands.chats.update import UpdateChatCommand
from app.chats.dtos.chats import ChatListItemDTO, ChatPresenceDTO
from app.chats.dtos.messages import MessageDeliveryStatusDTO
from app.chats.queries.chats.get_by_id import ChatDetailDTO, GetChatByIdQuery
from app.chats.queries.chats.get_my_list import GetChatsQuery
from app.chats.queries.chats.presence import GetChatPresenceQuery, GetMessageDeliveryQuery
from app.chats.schemas.chats.request import (
    AddMemberRequest,
    BanRequest,
    ChangeRoleRequest,
    CreateChatRequest,
    CreateChatResponse,
    GetChatsRequest,
    UpdateChatRequest
)
from app.core.db.repository import PageResult
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat — direct DM or group/channel",
)
async def create_chat(
    request: CreateChatRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> CreateChatResponse:
    results = await mediator.handle_command(
        CreateChatCommand(
            user_jwt_data=user_jwt_data,
            chat_type=request.chat_type,
            member_ids=request.member_ids,
            name=request.name,
            description=request.description,
            is_public=request.is_public,
        )
    )
    result = next(iter(results))
    return CreateChatResponse(chat_id=result.chat_id)


@router.get(
    "/my",
    status_code=status.HTTP_200_OK,
    summary="List user's chats with unread counts (bulk Redis fetch)",
)
async def get_chats(
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
    params: GetChatsRequest = Query(...),
) -> PageResult[ChatListItemDTO]:
    return await mediator.handle_query(
        GetChatsQuery(
            user_jwt_data=user_jwt_data,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.get(
    "/{chat_id}",
    status_code=status.HTTP_200_OK,
    summary="Get chat details with members list",
)
async def get_chat(
    chat_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ChatDetailDTO:
    return await mediator.handle_query(
        GetChatByIdQuery(user_jwt_data=user_jwt_data, chat_id=chat_id)
    )


@router.post(
    "/{chat_id}/members",
    status_code=status.HTTP_200_OK,
    summary="Add a user to a group/channel chat",
)
async def add_member(
    chat_id: int,
    request: AddMemberRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        AddMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=request.user_id,
            role=request.role,
        )
    )


@router.put(
    "/{chat_id}",
    status_code=status.HTTP_200_OK,
    summary="Update chat name / description / avatar",
)
async def update_chat(
    chat_id: int,
    request: UpdateChatRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        UpdateChatCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            name=request.name,
            description=request.description,
            avatar_url=request.avatar_url,
        )
    )


@router.put(
    "/{chat_id}/members/{user_id}/role",
    status_code=status.HTTP_200_OK,
    summary="Change member role",
)
async def change_member_role(
    chat_id: int,
    user_id: int,
    request: ChangeRoleRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        ChangeMemberRoleCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
            new_role=request.role,
        )
    )


@router.delete(
    "/{chat_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Kick member from chat",
)
async def remove_member(
    chat_id: int,
    user_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        KickMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
        )
    )


@router.post(
    "/{chat_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave chat",
)
async def leave_chat(
    chat_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        LeaveChatCommand(user_jwt_data=user_jwt_data, chat_id=chat_id)
    )


@router.post(
    "/{chat_id}/members/{user_id}/ban",
    status_code=status.HTTP_200_OK,
    summary="Ban or unban member",
)
async def ban_member(
    chat_id: int,
    user_id: int,
    request: BanRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        BanMemberCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            target_user_id=user_id,
            ban=request.ban,
        )
    )

@router.get(
    "/{chat_id}/presence",
    status_code=status.HTTP_200_OK,
    summary="Online status for all chat members",
)
async def get_chat_presence(
    chat_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ChatPresenceDTO:
    return await mediator.handle_query(
        GetChatPresenceQuery(user_jwt_data=user_jwt_data, chat_id=chat_id)
    )


@router.get(
    "/{chat_id}/messages/{message_id}/delivery",
    status_code=status.HTTP_200_OK,
    summary="Delivery status of a specific message",
)
async def get_message_delivery(
    chat_id: int,
    message_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> MessageDeliveryStatusDTO:
    return await mediator.handle_query(
        GetMessageDeliveryQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
        )
    )