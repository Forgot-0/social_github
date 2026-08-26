from prometheus_client import Counter

DELIVERY_ROUTER_STREAM_ENTRIES = Counter(
    "chat_delivery_router_stream_entries_total",
    "Entries pushed by ChatDeliveryRouter into gateway Redis Streams",
    labelnames=("strategy",),
)

DELIVERY_ROUTER_OFFLINE_SIGNALS = Counter(
    "chat_delivery_router_offline_signals_total",
    "Offline-recipients signals published to the notifications topic, by result",
    labelnames=("result",),
)

DELIVERY_ROUTER_OFFLINE_RECIPIENTS = Counter(
    "chat_delivery_router_offline_recipients_total",
    "Number of offline recipients reported to the notifications topic",
)
