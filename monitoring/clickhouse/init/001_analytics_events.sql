CREATE DATABASE IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.analytics_events
(
    event_time DateTime,
    event_name LowCardinality(String),
    event_id UUID,
    actor_id UInt64,
    entity_id UInt64,
    source LowCardinality(String),
    payload JSON
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_name, event_time, actor_id);
