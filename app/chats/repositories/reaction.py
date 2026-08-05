from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID, uuid7

from sqlalchemy import Select, func, select, text
from sqlalchemy.dialects.postgresql import insert

from app.chats.models.reaction import MessageReaction, MessageReactionCounter
from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter
from app.core.utils import now_utc

SET_REACTION_SQL = text(
    """
    WITH old AS (
        SELECT emoji
        FROM message_reactions
        WHERE message_id = :message_id AND user_id = :user_id
        FOR UPDATE
    ), upserted AS (
        INSERT INTO message_reactions (id, chat_id, message_id, user_id, emoji, created_at, updated_at)
        VALUES (:id, :chat_id, :message_id, :user_id, :emoji, :now, :now)
        ON CONFLICT (message_id, user_id)
        DO UPDATE SET emoji = EXCLUDED.emoji, updated_at = EXCLUDED.updated_at
        RETURNING emoji
    )
    SELECT (SELECT emoji FROM old) AS old_emoji,
           (SELECT emoji FROM upserted) AS new_emoji
    """
)

DELETE_REACTION_SQL = text(
    """
    DELETE FROM message_reactions
    WHERE message_id = :message_id AND user_id = :user_id AND emoji = :emoji
    RETURNING emoji
    """
)


@dataclass
class MessageReactionRepository(IRepository[MessageReaction]):

    async def set_reaction(
        self,
        chat_id: UUID,
        message_id: UUID,
        user_id: int,
        emoji: str,
    ) -> tuple[str | None, bool]:
        result = await self.session.execute(
            SET_REACTION_SQL,
            {
                "id": uuid7(),
                "chat_id": chat_id,
                "message_id": message_id,
                "user_id": user_id,
                "emoji": emoji,
                "now": now_utc(),
            },
        )

        row = result.one()
        old_emoji: str | None = row.old_emoji

        if old_emoji == emoji:
            return old_emoji, False

        if old_emoji is not None:
            await self._decrement_counter(message_id, old_emoji)

        await self._increment_counter(message_id, emoji)
        return old_emoji, True

    async def remove_reaction(
        self,
        message_id: UUID,
        user_id: int,
        emoji: str,
    ) -> bool:
        result = await self.session.execute(
            DELETE_REACTION_SQL,
            {"message_id": message_id, "user_id": user_id, "emoji": emoji},
        )
        removed = result.first() is not None

        if removed:
            await self._decrement_counter(message_id, emoji)

        return removed

    async def _increment_counter(self, message_id: UUID, emoji: str) -> None:
        stmt = (
            insert(MessageReactionCounter)
            .values(message_id=message_id, emoji=emoji, count=1, updated_at=now_utc())
            .on_conflict_do_update(
                index_elements=[
                    MessageReactionCounter.message_id,
                    MessageReactionCounter.emoji,
                ],
                set_={
                    "count": MessageReactionCounter.count + 1,
                    "updated_at": now_utc(),
                },
            )
        )
        await self.session.execute(stmt)

    async def _decrement_counter(self, message_id: UUID, emoji: str) -> None:
        await self.session.execute(
            text(
                """
                UPDATE message_reaction_counters
                SET count = GREATEST(0, count - 1), updated_at = :now
                WHERE message_id = :message_id AND emoji = :emoji
                """
            ),
            {"message_id": message_id, "emoji": emoji, "now": now_utc()},
        )

    async def get_counter(self, message_id: UUID, emoji: str) -> int:
        stmt = select(MessageReactionCounter.count).where(
            MessageReactionCounter.message_id == message_id,
            MessageReactionCounter.emoji == emoji,
        )
        result = await self.session.execute(stmt)
        value = result.scalar()
        return int(value or 0)

    async def count_distinct_emojis(self, message_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(MessageReactionCounter)
            .where(
                MessageReactionCounter.message_id == message_id,
                MessageReactionCounter.count > 0,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_counters_for_messages(
        self, message_ids: Sequence[UUID]
    ) -> list[MessageReactionCounter]:
        if not message_ids:
            return []

        stmt = (
            select(MessageReactionCounter)
            .where(
                MessageReactionCounter.message_id.in_(list(message_ids)),
                MessageReactionCounter.count > 0,
            )
            .order_by(MessageReactionCounter.message_id, MessageReactionCounter.emoji)
        )
        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_user_reactions_for_messages(
        self, message_ids: Sequence[UUID], user_id: int
    ) -> list[MessageReaction]:
        if not message_ids:
            return []

        stmt = select(MessageReaction).where(
            MessageReaction.message_id.in_(list(message_ids)),
            MessageReaction.user_id == user_id,
        )
        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_users_by_emoji(
        self,
        message_id: UUID,
        emoji: str,
        limit: int,
        cursor_user_id: int | None = None,
    ) -> list[MessageReaction]:
        stmt = (
            select(MessageReaction)
            .where(
                MessageReaction.message_id == message_id,
                MessageReaction.emoji == emoji,
            )
            .order_by(MessageReaction.user_id.asc())
            .limit(limit + 1)
        )

        if cursor_user_id is not None:
            stmt = stmt.where(MessageReaction.user_id > cursor_user_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
