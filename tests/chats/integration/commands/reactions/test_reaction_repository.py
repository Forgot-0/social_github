import pytest

from app.chats.models.chat import Chat
from app.chats.models.reaction import MessageReactionCounter
from app.chats.repositories.reaction import MessageReactionRepository
from app.core.services.auth.dto import UserJWTData

pytestmark = [pytest.mark.integration, pytest.mark.chats, pytest.mark.asyncio]


async def test_duplicate_add_returns_none(
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")

    assert await reaction_repository.add_reaction(
        chat_id=group_chat.id, message_id=message.id, user_id=1, emoji="👍"
    ) is not None
    assert await reaction_repository.add_reaction(
        chat_id=group_chat.id, message_id=message.id, user_id=1, emoji="👍"
    ) is None


async def test_recount_rebuilds_counters(
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
    db_session,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    for uid in (1, 2):
        await reaction_repository.add_reaction(
            chat_id=group_chat.id, message_id=message.id, user_id=uid, emoji="🔥"
        )

    await db_session.execute(
        MessageReactionCounter.__table__.update()
        .where(MessageReactionCounter.message_id == message.id)
        .values(count=99)
    )
    await reaction_repository.recount(message.id)

    groups = {g.emoji: g.count for g in await reaction_repository.get_current_groups(message.id)}
    assert groups == {"🔥": 2}


async def test_recent_reactors_are_most_recent_first(
    reaction_repository: MessageReactionRepository,
    group_chat: Chat,
    user_jwt: UserJWTData,
    create_message,
) -> None:
    message = await create_message(group_chat, user_jwt, "hi")
    for uid in (10, 11, 12, 13):
        await reaction_repository.add_reaction(
            chat_id=group_chat.id, message_id=message.id, user_id=uid, emoji="👍"
        )

    state = await reaction_repository.get_reaction_state_for_messages([message.id], 10)
    recent = state[message.id].recent_by_emoji["👍"]
    assert len(recent) <= 3
    assert 13 in recent
