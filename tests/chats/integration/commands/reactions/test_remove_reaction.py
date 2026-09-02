import pytest
from dishka import AsyncContainer

from app.chats.commands.reactions.remove import (
    RemoveReactionCommand,
    RemoveReactionCommandHandler,
)
from app.chats.commands.reactions.set import SetReactionCommand, SetReactionCommandHandler
from app.chats.models.chat import Chat
from app.chats.repositories.reaction import MessageReactionRepository
from app.core.services.auth.dto import UserJWTData

pytestmark = [pytest.mark.integration, pytest.mark.chats, pytest.mark.asyncio]


@pytest.fixture
async def set_handler(request_container: AsyncContainer) -> SetReactionCommandHandler:
    return await request_container.get(SetReactionCommandHandler)


@pytest.fixture
async def remove_handler(request_container: AsyncContainer) -> RemoveReactionCommandHandler:
    return await request_container.get(RemoveReactionCommandHandler)


async def test_remove_existing_reaction_drops_counter_row(
    set_handler: SetReactionCommandHandler,
    remove_handler: RemoveReactionCommandHandler,
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    await set_handler.handle(
        SetReactionCommand(
            chat_id=group_chat.id, message_id=message.id, emoji="👍", user_jwt_data=user_jwt
        )
    )

    await remove_handler.handle(
        RemoveReactionCommand(
            chat_id=group_chat.id, message_id=message.id, emoji="👍", user_jwt_data=user_jwt
        )
    )

    assert await reaction_repository.get_current_groups(message.id) == []
    assert await reaction_repository.count_distinct_emojis(message.id) == 0


async def test_remove_absent_reaction_is_noop(
    remove_handler: RemoveReactionCommandHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    await remove_handler.handle(
        RemoveReactionCommand(
            chat_id=group_chat.id, message_id=message.id, emoji="👍", user_jwt_data=user_jwt
        )
    )


async def test_remove_one_of_many_keeps_others(
    set_handler: SetReactionCommandHandler,
    remove_handler: RemoveReactionCommandHandler,
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    make_user_jwt,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    await set_handler.handle(
        SetReactionCommand(
            chat_id=group_chat.id, message_id=message.id, emoji="👍", user_jwt_data=user_jwt
        )
    )
    await set_handler.handle(
        SetReactionCommand(
            chat_id=group_chat.id,
            message_id=message.id,
            emoji="👍",
            user_jwt_data=make_user_jwt(id="2"),
        )
    )

    await remove_handler.handle(
        RemoveReactionCommand(
            chat_id=group_chat.id, message_id=message.id, emoji="👍", user_jwt_data=user_jwt
        )
    )

    groups = await reaction_repository.get_current_groups(message.id)
    assert [(g.emoji, g.count) for g in groups] == [("👍", 1)]
