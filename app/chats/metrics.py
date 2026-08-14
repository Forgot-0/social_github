"""Prometheus metrics for the chat websocket gateway and delivery pipeline.

Registration follows the same pattern as ``app/core/outbox/metrics.py``:
module level collectors on the default registry. The FastAPI process exposes
them through ``PrometheusFastApiInstrumentator(...).expose(app)`` (multiprocess
aware via ``PROMETHEUS_MULTIPROC_DIR``), so nothing extra has to be wired in
``app/main.py``.

The consumers process (``app/consumers.py``) exposes its own
``CollectorRegistry`` for ``KafkaPrometheusMiddleware``; collectors that are
incremented there are created with an explicit ``registry`` argument instead,
see ``register_delivery_router_metrics``.
"""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

WS_ACTIVE_CONNECTIONS = Gauge(
    "chat_ws_active_connections",
    "Number of websocket connections currently registered on this gateway",
    labelnames=("gateway_id",),
    multiprocess_mode="livesum",
)

WS_ACTIVE_USERS = Gauge(
    "chat_ws_active_users",
    "Number of distinct users with at least one websocket connection on this gateway",
    labelnames=("gateway_id",),
    multiprocess_mode="livesum",
)

WS_SUBSCRIBED_CHATS = Gauge(
    "chat_ws_subscribed_chats",
    "Number of chats with at least one local websocket subscriber on this gateway",
    labelnames=("gateway_id",),
    multiprocess_mode="livesum",
)

# Origin -> websocket frame. "Origin" is the domain event ``created_at``, i.e.
# the moment the event was staged into the outbox by MediatorEventBus.publish.
# Measured server side only: outbox -> debezium -> kafka -> delivery router ->
# redis gateway stream -> ChatConnectionManager frame enqueue.
WS_DELIVERY_LATENCY = Histogram(
    "chat_ws_delivery_latency_seconds",
    "Latency from domain event creation (outbox) to websocket frame enqueue",
    labelnames=("fanout_strategy", "event_type"),
    buckets=(
        0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75,
        1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0,
    ),
)

WS_GATEWAY_STREAM_BACKLOG = Gauge(
    "chat_ws_gateway_stream_backlog",
    "XLEN of the redis gateway stream for this gateway",
    labelnames=("gateway_id",),
    multiprocess_mode="max",
)

WS_GATEWAY_STREAM_PENDING = Gauge(
    "chat_ws_gateway_stream_pending",
    "Number of unacked entries in the gateway stream consumer group",
    labelnames=("gateway_id",),
    multiprocess_mode="max",
)

WS_FRAMES_DROPPED = Counter(
    "chat_ws_frames_dropped_total",
    "Websocket frames dropped because the send queue was full (slow consumer)",
    labelnames=("gateway_id",),
)


def register_delivery_router_metrics(registry: CollectorRegistry) -> "DeliveryRouterMetrics":
    """Build delivery-router collectors bound to the consumers registry.

    Called from ``app/consumers.py`` with the same registry that
    ``KafkaPrometheusMiddleware`` uses, so the existing ``/metrics`` ASGI route
    exposes them without a second endpoint.
    """
    return DeliveryRouterMetrics(
        enqueue_latency=Histogram(
            "chat_delivery_router_enqueue_latency_seconds",
            "Latency from domain event creation (outbox) to redis gateway stream XADD",
            labelnames=("fanout_strategy",),
            buckets=(
                0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75,
                1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0,
            ),
            registry=registry,
        ),
        stream_entries=Counter(
            "chat_delivery_router_stream_entries_total",
            "Gateway stream entries produced by the delivery router",
            labelnames=("fanout_strategy",),
            registry=registry,
        ),
        recipients=Counter(
            "chat_delivery_router_recipients_total",
            "Recipient user ids fanned out by the delivery router",
            labelnames=("fanout_strategy",),
            registry=registry,
        ),
    )


class DeliveryRouterMetrics:
    """Holder so the router can stay ignorant of which registry it writes to."""

    __slots__ = ("enqueue_latency", "recipients", "stream_entries")

    def __init__(
        self,
        enqueue_latency: Histogram,
        stream_entries: Counter,
        recipients: Counter,
    ) -> None:
        self.enqueue_latency = enqueue_latency
        self.stream_entries = stream_entries
        self.recipients = recipients


_delivery_router_metrics: DeliveryRouterMetrics | None = None


def set_delivery_router_metrics(metrics: DeliveryRouterMetrics) -> None:
    global _delivery_router_metrics  # noqa: PLW0603
    _delivery_router_metrics = metrics


def get_delivery_router_metrics() -> DeliveryRouterMetrics | None:
    return _delivery_router_metrics
