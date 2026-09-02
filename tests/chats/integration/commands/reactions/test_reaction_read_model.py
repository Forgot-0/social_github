import pytest
from dishka import AsyncContainer

from app.chats.commands.reactions.set import SetReactionCommand, SetReactionCommandHandler
from app.chats.models.chat import Chat
from app.chats.queries.messages.get_list import GetMessagesQuery, GetMessagesQueryHandler
from app.chats.queries.reactions.get_list import (
    GetMessageReactionsQuery,
    GetMessageReactionsQueryHandler,
)
from app.core.services.auth.dto import UserJWTData

pytestmark = [pytest.mark.integration, pytest.mark.chats, pytest.mark.asyncio]


@pytest.fixture
async def set_handler(request_container: AsyncContainer) -> SetReactionCommandHandler:
    return await request_container.get(SetReactionCommandHandler)


@pytest.fixture
async def messages_handler(request_container: AsyncContainer) -> GetMessagesQueryHandler:
    return await request_container.get(GetMessagesQueryHandler)


@pytest.fixture
async def reactions_handler(
    request_container: AsyncContainer,
) -> GetMessageReactionsQueryHandler:
    return await request_container.get(GetMessageReactionsQueryHandler)


async def test_message_list_carries_reaction_groups_sorted_by_count(
    set_handler: SetReactionCommandHandler,
    messages_handler: GetMessagesQueryHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    make_user_jwt,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    await set_handler.handle(
        SetReactionCommand(
            chat_id=group_chat.id, message_id=message.id, emoji="🔥", user_jwt_data=user_jwt
        )
    )
    for uid in ("2", "3"):
        await set_handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji="👍",
                user_jwt_data=make_user_jwt(id=uid),
            )
        )

    result = await messages_handler.handle(
        GetMessagesQuery(user_jwt_data=user_jwt, chat_id=group_chat.id)
    )
    reactions = result.messages[0].reactions
    assert [(g.emoji, g.count) for g in reactions] == [("👍", 2), ("🔥", 1)]

    fire = next(g for g in reactions if g.emoji == "🔥")
    thumb = next(g for g in reactions if g.emoji == "👍")
    assert fire.reacted_by_me is True
    assert thumb.reacted_by_me is False


async def test_reactions_query_returns_users_for_emoji(
    set_handler: SetReactionCommandHandler,
    reactions_handler: GetMessageReactionsQueryHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    make_user_jwt,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    for jwt in (user_jwt, make_user_jwt(id="2")):
        await set_handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji="👍",
                user_jwt_data=jwt,
            )
        )

    result = await reactions_handler.handle(
        GetMessageReactionsQuery(
            user_jwt_data=user_jwt,
            chat_id=group_chat.id,
            message_id=message.id,
            emoji="👍",
        )
    )
    assert set(result.users) == {1, 2}
    assert [(g.emoji, g.count) for g in result.groups] == [("👍", 2)]
