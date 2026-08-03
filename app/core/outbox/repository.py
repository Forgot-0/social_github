from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.configs.app import app_config
from app.core.outbox.model import OutboxMessage, OutboxStatus
from app.core.utils import now_utc


@dataclass
class OutboxRepository:
    session: AsyncSession

    async def create(self, outbox_message: OutboxMessage) -> None:
        self.session.add(outbox_message)

    async def fetch_batch_for_publish(self, limit: int | None = None) -> Sequence[OutboxMessage]:
        stmt = (
            select(OutboxMessage)
            .where(
                OutboxMessage.status == OutboxStatus.PENDING,
                OutboxMessage.available_at <= now_utc(),
            )
            .order_by(OutboxMessage.id)
            .limit(limit or app_config.OUTBOX_BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_pending(self) -> int:
        stmt = select(func.count()).select_from(OutboxMessage).where(
            OutboxMessage.status == OutboxStatus.PENDING
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def count_failed(self) -> int:
        stmt = select(func.count()).select_from(OutboxMessage).where(
            OutboxMessage.status == OutboxStatus.FAILED
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def oldest_pending_age_seconds(self) -> float:
        stmt = select(func.min(OutboxMessage.created_at)).where(
            OutboxMessage.status == OutboxStatus.PENDING
        )
        result = await self.session.execute(stmt)
        oldest = result.scalar_one_or_none()

        if oldest is None:
            return 0.0

        return max(0.0, (now_utc() - oldest).total_seconds())

    async def cleanup_published(self, retention_days: int | None = None) -> None:
        threshold = now_utc() - timedelta(
            days=retention_days or app_config.OUTBOX_RETENTION_DAYS
        )
        subquery = (
            select(OutboxMessage.id)
            .where(
                OutboxMessage.status == OutboxStatus.PUBLISHED,
                OutboxMessage.published_at < threshold,
            )
            .limit(app_config.OUTBOX_CLEANUP_BATCH_SIZE)
            .scalar_subquery()
        )
        stmt = delete(OutboxMessage).where(OutboxMessage.id.in_(subquery))

        await self.session.execute(stmt)
        await self.session.commit()

    async def requeue_failed(self, limit: int = 1_000) -> int:
        stmt = (
            select(OutboxMessage)
            .where(OutboxMessage.status == OutboxStatus.FAILED)
            .order_by(OutboxMessage.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        messages = result.scalars().all()

        for message in messages:
            message.status = OutboxStatus.PENDING
            message.attempts = 0
            message.available_at = now_utc()

        await self.session.commit()
        return len(messages)
