# Chats module highload audit (target: 10M users)

Date: 2026-03-24

## Executive summary

Current `app/chats` implementation is **not production-ready** for a 10M user scale without architecture and data-path changes.

Main blockers:
- fan-out model (`publish_bulk` per recipient) scales linearly per message for large chats;
- read receipts flush worker can lose updates due to unordered upsert;
- Redis key model (`unread:{user}:{chat}`, `presence:user:*`, delivery zsets) will explode in key cardinality at 10M DAU;
- expensive queries on chat list and message list do not fully use optimal composite/partial indexes;
- websocket runtime keeps large in-memory maps and per-user heartbeat tasks.

## Findings

## 1) O(n) fan-out for every message (critical)
- `SendedMessageEventHandler` fetches all member ids and calls `publish_bulk` to user channels for each recipient.
- For channels with large audience this becomes `O(number_of_members)` network operations per message.

### Why this breaks at highload
Large chat/channel (100k+ members) means one message produces 100k publish operations and unread increments.

### Recommended fix
- Introduce **chat-level pub/sub channel** for broadcast (`chat:{id}:channel`) and subscribe users by chat membership on websocket node.
- Keep per-user channel only for personal events (kicked, security, system).
- For unread counters use asynchronous aggregation pipeline (Kafka/NATS + worker), not inline per-recipient increments.

## 2) Unread counters incremented one-by-one in Redis pipeline (critical)
- `increment_unread_bulk` loops through each user and runs `INCRBY` per user key.

### Why this breaks at highload
Huge CPU/network overhead with millions of keys and massive per-message command count.

### Recommended fix
- Replace per-user immediate counters with batched event stream and periodic materialization.
- Add Lua script or Redis function for grouped increments per chat shard if real-time strictness is required.

## 3) Read receipts flush may overwrite newer values with older values (critical correctness)
- `mark_read` enqueues `user:chat:message` records into sorted set.
- `FlushReadReceiptsTask` upserts without monotonic guard (`set last_read_message_id = excluded` always).

### Why this breaks
Out-of-order tasks can move cursor backwards and corrupt read state.

### Recommended fix
- Use `ON CONFLICT ... DO UPDATE ... WHERE read_receipts.last_read_message_id < excluded.last_read_message_id`.
- Also deduplicate by `(user_id, chat_id)` before insert (keep max message_id in batch).

## 4) Pending read receipts queue can become infinite backlog (high)
- Single cron every 5 seconds with fixed batch 5000.

### Why this breaks
At high write rate backlog grows unbounded, memory pressure and stale read state.

### Recommended fix
- Horizontal consumers by shard key.
- Adaptive batch size + lag metrics + dead-letter handling.
- Move from redis zset queue to durable log (Kafka/Redis Streams).

## 5) High-cardinality Redis keys for unread counters (critical)
- Key format: `unread:{user_id}:{chat_id}`.

### Why this breaks
Potentially billions of keys (user x chat), huge memory + eviction risk.

### Recommended fix
- Keep unread in compact per-user hash (e.g., `unread:{user}` hash field=`chat_id`) with TTL policy and compression strategy.
- Archive cold chats to DB snapshots.

## 6) Presence model key-per-user with frequent EXPIRE refresh (high)
- Presence uses `setex` and periodic `expire` refresh.

### Why this breaks
Heartbeat churn at scale creates large write amplification.

### Recommended fix
- Store presence in time-bucket structures (sorted set score=last_seen) and compute online by threshold.
- Reduce heartbeat frequency with server push pings + client adaptive keepalive.

## 7) Websocket connection manager stores all sockets in process memory (high)
- `connections_map` is in-memory per worker; each user key has set of WebSocket objects.

### Why this breaks
Memory footprint and uneven load across workers; no global awareness of exact connection count.

### Recommended fix
- Add external connection registry (Redis/etcd) for global control.
- Bound max connections per node and enforce load-shedding.
- Move heartbeat to shared scheduler instead of per-key tasks.

## 8) One heartbeat task per user channel (high)
- `_ensure_heartbeat` creates task per key.

### Why this breaks
Millions of tasks are impossible; scheduler overhead and memory blowup.

### Recommended fix
- Replace with a single periodic sweep loop per process.
- Use websocket ping frames managed by ASGI server/proxy when possible.

## 9) Potential race/KeyError in connection cleanup (medium)
- `remove_connection` uses `self.lock_map[key]` directly and assumes key exists.

### Why this matters
Concurrent disconnect paths may raise and leak resources under load spikes.

### Recommended fix
- Use `lock = self.lock_map.get(key)` guard; idempotent cleanup semantics.

## 10) Chat list query uses distinct + count(subquery) (high)
- `get_user_chats` builds distinct ordered query and separate count from subquery.

### Why this breaks
Expensive sort/distinct on large memberships table; poor latency for active users.

### Recommended fix
- Keyset pagination by `(last_activity_at, id)`.
- Denormalized `user_chat_index` table (materialized feed per user).
- Add covering index for membership filter + active chat ordering path.

## 11) Message list loads read cursors for all members of chat (high)
- `GetMessagesQuery` fetches all member ids and all read cursors for each page request.

### Why this breaks
For big chats message history request becomes O(members), not O(page_size).

### Recommended fix
- Return aggregate read stats, not full map, for large chats.
- Provide separate endpoint for read details with paging.
- Hard cap detail mode to small groups.

## 12) No partitioning strategy for `messages` and `read_receipts` tables (critical)
- Growth is unbounded; hot writes and scans in same logical tables.

### Why this breaks
VACUUM/autovacuum pressure, index bloat, long checkpoints.

### Recommended fix
- Partition `messages` by `chat_id` hash or by time+chat hybrid.
- Partition `read_receipts` by `chat_id` hash.
- Add retention/archival policy for old messages.

## 13) Bare `raise` in `Chat.update_last_activity` (medium correctness)
- If message timestamp is older/equal, code does bare `raise`.

### Why this breaks
Can produce unexpected runtime error and rollback under concurrent message ordering anomalies.

### Recommended fix
- Replace with safe no-op or domain exception with monitoring counter.

## 14) Websocket auth token passed via query parameter (medium security/ops)
- WS endpoint accepts `token` in query string.

### Why this matters
Token leaks into logs, traces, proxies.

### Recommended fix
- Move token to `Authorization` header / websocket subprotocol / secure cookie.

## 15) Missing SLO-driven backpressure and load-shedding mechanisms (critical)
- No explicit per-chat throughput limits, queue lag protections, or graceful degradation modes.

### Recommended fix
- Add admission control by chat size/tier.
- Drop non-critical events first (typing, delivery details).
- Define SLOs per API and WS operations and enforce with circuit breakers.

## Suggested target architecture for 10M users

1. Transport layer:
- stateless websocket gateways;
- global session directory;
- chat channel subscription model.

2. Event backbone:
- durable stream (Kafka/NATS/Redis Streams) for message, unread, read, presence.

3. Data layer:
- partitioned Postgres/Citus/Scylla strategy for messages/reads;
- Redis only for hot ephemeral state.

4. Product semantics:
- degrade expensive features for very large chats (full per-user read map, realtime typing fan-out).

## Prioritized implementation roadmap

P0 (must):
- Fix monotonic read upsert.
- Replace per-recipient fan-out for large chats.
- Replace heartbeat-per-user model.
- Introduce queue lag metrics and autoscaling.

P1:
- Keyset pagination for chats/messages.
- Redesign unread key schema and compaction.
- Add partitioning for heavy tables.

P2:
- Delivery/read analytics pipeline and asynchronous materialized views.
- Adaptive feature degradation by chat tier.