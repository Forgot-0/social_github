from datetime import timedelta
from uuid import uuid4

import pytest
from dishka import AsyncContainer

from app.chats.commands.reactions.set import SetReactionCommand, SetReactionCommandHandler
from app.chats.exceptions import (
    AccessDeniedChatError,
    InvalidReactionError,
    NotFoundChatError,
    NotFoundMessageError,
    ReactionNotAllowedError,
    ReactionsDisabledError,
    TooManyReactionsError,
)
from app.chats.models.chat import Chat, ChatReactionsMode
from app.chats.repositories.chat import ChatRepository
from app.chats.repositories.reaction import MessageReactionRepository
from app.core.services.auth.dto import UserJWTData
from app.core.utils import now_utc

pytestmark = [pytest.mark.integration, pytest.mark.chats, pytest.mark.asyncio]


@pytest.fixture
async def handler(request_container: AsyncContainer) -> SetReactionCommandHandler:
    return await request_container.get(SetReactionCommandHandler)


async def test_adds_reaction_and_counter(
    handler: SetReactionCommandHandler,
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    await handler.handle(
        SetReactionCommand(
            chat_id=group_chat.id,
            message_id=message.id,
            emoji="👍",
            user_jwt_data=user_jwt,
        )
    )

    groups = await reaction_repository.get_current_groups(message.id)
    assert [(g.emoji, g.count) for g in groups] == [("👍", 1)]
    assert await reaction_repository.list_user_emojis(message.id, int(user_jwt.id)) == ["👍"]


async def test_same_emoji_twice_is_noop(
    handler: SetReactionCommandHandler,
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    cmd = SetReactionCommand(
        chat_id=group_chat.id, message_id=message.id, emoji="👍", user_jwt_data=user_jwt
    )

    await handler.handle(cmd)
    await handler.handle(cmd)

    groups = await reaction_repository.get_current_groups(message.id)
    assert [(g.emoji, g.count) for g in groups] == [("👍", 1)]


async def test_multiple_distinct_reactions_from_one_user(
    handler: SetReactionCommandHandler,
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    for emoji in ("👍", "🔥"):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji=emoji,
                user_jwt_data=user_jwt,
            )
        )

    assert set(
        await reaction_repository.list_user_emojis(message.id, int(user_jwt.id))
    ) == {"👍", "🔥"}


async def test_per_user_limit_enforced(
    handler: SetReactionCommandHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    for emoji in ("👍", "🔥", "❤️"):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji=emoji,
                user_jwt_data=user_jwt,
            )
        )

    with pytest.raises(TooManyReactionsError):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji="🎉",
                user_jwt_data=user_jwt,
            )
        )


async def test_unknown_emoji_rejected(
    handler: SetReactionCommandHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    with pytest.raises(InvalidReactionError):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji="not-an-emoji",
                user_jwt_data=user_jwt,
            )
        )


async def test_reactions_disabled_mode(
    handler: SetReactionCommandHandler,
    chat_repository: ChatRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
    db_session,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    group_chat.reactions_mode = ChatReactionsMode.NONE
    await db_session.commit()

    with pytest.raises(ReactionsDisabledError):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji="👍",
                user_jwt_data=user_jwt,
            )
        )


async def test_reactions_some_mode_restricts_set(
    handler: SetReactionCommandHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
    db_session,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    group_chat.reactions_mode = ChatReactionsMode.SOME
    group_chat.allowed_reactions = ["🔥"]
    await db_session.commit()

    with pytest.raises(ReactionNotAllowedError):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji="👍",
                user_jwt_data=user_jwt,
            )
        )

    await handler.handle(
        SetReactionCommand(
            chat_id=group_chat.id,
            message_id=message.id,
            emoji="🔥",
            user_jwt_data=user_jwt,
        )
    )


async def test_muted_member_cannot_react(
    handler: SetReactionCommandHandler,
    chat_repository: ChatRepository,
    group_chat: Chat,
    make_user_jwt,
    create_message,
    user_jwt: UserJWTData,
    db_session,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    member = await chat_repository.get_member_chat(group_chat.id, 2, with_role=False)
    member.muted_to = now_utc() + timedelta(hours=1)
    await db_session.commit()

    with pytest.raises(AccessDeniedChatError):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji="👍",
                user_jwt_data=make_user_jwt(id="2"),
            )
        )


async def test_non_member_rejected(
    handler: SetReactionCommandHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
    make_user_jwt,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    with pytest.raises(NotFoundChatError):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=message.id,
                emoji="👍",
                user_jwt_data=make_user_jwt(id="999"),
            )
        )


async def test_unknown_message_rejected(
    handler: SetReactionCommandHandler,
    group_chat: Chat,
    user_jwt: UserJWTData,
) -> None:
    with pytest.raises(NotFoundMessageError):
        await handler.handle(
            SetReactionCommand(
                chat_id=group_chat.id,
                message_id=uuid4(),
                emoji="👍",
                user_jwt_data=user_jwt,
            )
        )
