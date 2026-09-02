import pytest
from dishka import AsyncContainer

from app.chats.commands.reactions.set_many import (
    SetReactionsCommand,
    SetReactionsCommandHandler,
)
from app.chats.exceptions import InvalidReactionError, TooManyReactionsError
from app.chats.models.chat import Chat
from app.chats.repositories.reaction import MessageReactionRepository
from app.core.services.auth.dto import UserJWTData

pytestmark = [pytest.mark.integration, pytest.mark.chats, pytest.mark.asyncio]


@pytest.fixture
async def handler(request_container: AsyncContainer) -> SetReactionsCommandHandler:
    return await request_container.get(SetReactionsCommandHandler)


async def test_replace_set(
    handler: SetReactionsCommandHandler,
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    await handler.handle(
        SetReactionsCommand(
            chat_id=group_chat.id,
            message_id=message.id,
            emojis=("👍", "🔥"),
            user_jwt_data=user_jwt,
        )
    )
    await handler.handle(
        SetReactionsCommand(
            chat_id=group_chat.id,
            message_id=message.id,
            emojis=("❤️",),
            user_jwt_data=user_jwt,
        )
    )

    assert await reaction_repository.list_user_emojis(message.id, int(user_jwt.id)) == ["❤️"]
    groups = {g.emoji: g.count for g in await reaction_repository.get_current_groups(message.id)}
    assert groups == {"❤️": 1}


async def test_empty_set_clears_all(
    handler: SetReactionsCommandHandler,
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    await handler.handle(
        SetReactionsCommand(
            chat_id=group_chat.id,
            message_id=message.id,
            emojis=("👍",),
            user_jwt_data=user_jwt,
        )
    )

    await handler.handle(
        SetReactionsCommand(
            chat_id=group_chat.id,
            message_id=message.id,
            emojis=(),
            user_jwt_data=user_jwt,
        )
    )

    assert await reaction_repository.get_current_groups(message.id) == []


async def test_set_exceeding_per_user_limit(
    handler: SetReactionsCommandHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    with pytest.raises(TooManyReactionsError):
        await handler.handle(
            SetReactionsCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emojis=("👍", "🔥", "❤️", "🎉"),
                user_jwt_data=user_jwt,
            )
        )


async def test_set_with_unknown_emoji(
    handler: SetReactionsCommandHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    with pytest.raises(InvalidReactionError):
        await handler.handle(
            SetReactionsCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emojis=("👍", "bogus"),
                user_jwt_data=user_jwt,
            )
        )
