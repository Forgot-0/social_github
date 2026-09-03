from prometheus_client import Counter, Histogram

CHAT_REACTION_COALESCE_COLLAPSED = Histogram(
    "chat_reaction_coalesce_collapsed",
    "Number of reaction events collapsed into a single fan-out by the coalescer",
    buckets=(1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144),
)

CHAT_REACTION_FANOUT_TOTAL = Counter(
    "chat_reaction_fanout_total",
    "Reaction updates handed to the delivery router for fan-out",
    labelnames=("mode",),
)

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
