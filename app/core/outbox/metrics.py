from prometheus_client import Counter, Gauge

from app.core.outbox.repository import OutboxRepository


OUTBOX_PENDING_MESSAGES = Gauge(
    "outbox_pending_messages",
    "Number of outbox messages in PENDING status",
)
OUTBOX_FAILED_MESSAGES = Gauge(
    "outbox_failed_messages",
    "Number of outbox messages in FAILED status",
)
OUTBOX_OLDEST_PENDING_AGE_SECONDS = Gauge(
    "outbox_oldest_pending_age_seconds",
    "Age in seconds of the oldest PENDING outbox message",
)
OUTBOX_EVENTS_WRITTEN = Counter(
    "outbox_events_written_total",
    "Total number of domain events written to the outbox",
    labelnames=("topic", "event_name"),
)


async def update_outbox_metrics(repository: OutboxRepository) -> dict[str, float]:
    pending = await repository.count_pending()
    failed = await repository.count_failed()
    oldest_age = await repository.oldest_pending_age_seconds()

    OUTBOX_PENDING_MESSAGES.set(pending)
    OUTBOX_FAILED_MESSAGES.set(failed)
    OUTBOX_OLDEST_PENDING_AGE_SECONDS.set(oldest_age)

    snapshot = {
        "pending": float(pending),
        "failed": float(failed),
        "oldest_pending_age_seconds": oldest_age,
    }
    return snapshot
