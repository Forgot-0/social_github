# Chats module: production highload performance audit

## Scope
- Reviewed hot paths in message send/read flow, chat list/messages queries, websocket fanout and Redis routing.
- Focused on bottlenecks that become critical under high RPS / high concurrent sockets.

## Critical bottlenecks (P0)

1. **N+1 Redis `SMEMBERS` lookups during fanout on write**
   - In `ChatDeliveryRouter._lookup_online_routes`, per-user `SMEMBERS` is queued in pipeline (`O(batch_users)` Redis calls per delivery batch).
   - Under large groups this amplifies fanout latency and Redis CPU.
   - Evidence: `pipe.smembers(WebsocketKeys.user_route_key(user_id))` inside a loop.

2. **Full-set scan of active subscribers for each event**
   - In active-subscriber mode, `_iter_active_subscriber_routes` iterates Redis set with `sscan_iter`, then `_validate_active_subscriber_batch` performs `EXISTS` for every connection key.
   - This is effectively `O(subscribers)` per event and scales poorly for hot chats/channels.
   - Also creates background cleanup tasks per stale chunk.

3. **Write amplification to Redis per subscribe/unsubscribe**
   - `subscribe_chat` writes several keys (`SADD`/`EXPIRE` twice + `SETEX`) for each subscription.
   - `unsubscribe_chat` removes several keys.
   - At high websocket churn this becomes dominant Redis traffic.

4. **Potential DB connection/transaction hold during event publish after commit**
   - In `SendMessageCommandHandler`, transaction commits and then immediately publishes events in request path.
   - If event bus is slow/backpressured, API latency grows directly.

## High impact bottlenecks (P1)

5. **Extra DB round-trips in send path**
   - Send message performs sequential operations: chat fetch, membership fetch, optional attachments fetch, optional reply message fetch, sequence allocation update, insert message.
   - For high QPS this creates a long critical path and increased p99.

6. **Per-request presigned URL generation burst**
   - `attach_download_urls` calls `generate_presigned_url` for each distinct attachment key via `asyncio.gather`.
   - For large pages/forwards this may create many concurrent storage calls and extra latency.

7. **Message list eager loading cost for every page**
   - `get_paginated_chat_messages` always loads `reply_to`, `attachments`, `forwarded_from` with `selectinload`.
   - This is useful functionally, but for large pages and heavy traffic creates additional SQL and memory pressure.

8. **Read receipts upsert on every read marker update**
   - `mark_read` always executes upsert; for frequent client read-pointer updates this can become write-heavy.
   - No buffering/debouncing layer visible in module.

## Medium bottlenecks (P2)

9. **Lock contention in local websocket manager**
   - `ChatConnectionManager` protects connection maps with one global async lock.
   - Under high concurrent connect/disconnect/subscribe/send-local operations this can become serialization point.

10. **Potential CPU overhead from sorting user sets before chunking**
   - `_enqueue_gateway_deliveries` sorts `user_ids` for each gateway before chunking.
   - Deterministic order is nice, but for very large sets this is avoidable CPU.

11. **Missing explicit index for read path cursor filter on `read_receipts` usage patterns**
   - Model has unique `(chat_id, user_id)` which is good for upsert.
   - If additional read patterns by `user_id` dominate elsewhere, may need covering index (outside this module usage verify with real query stats).

## Recommendations (priority order)

### P0 actions
1. Replace per-user `SMEMBERS` route lookup with compact per-gateway/per-user bitmap or hash strategy (or store gateway route in a single key to reduce lookup fanout).
2. For active-subscribers strategy, stop scanning whole subscriber set per event:
   - maintain gateway-local subscriber shards;
   - push only to gateways from `active_subscription_gateways_key(chat_id)`;
   - validate liveness lazily/periodically, not per event.
3. Reduce subscription write amplification:
   - avoid frequent `EXPIRE` refresh on every subscribe when unchanged;
   - consider batched heartbeat-based TTL refresh.
4. Decouple event publish from sync HTTP path (outbox/table + async dispatcher) to isolate API latency from broker latency.

### P1 actions
5. Collapse send-path checks into fewer queries where safe (membership + permissions hints; reply-in-chat validation in same query).
6. Add bounded concurrency/caching for presigned URLs (short-lived cache by `s3_key`, fanout-safe semaphore).
7. Make message query loading strategy adaptive (light list endpoint + detail hydration on demand).
8. Throttle/debounce read pointer updates (e.g., minimum seq delta/time window).

### P2 actions
9. Split websocket manager lock or move to lock-free per-user/per-chat structures where possible.
10. Remove sort in delivery unless strict ordering is required.
11. Validate indexes with `EXPLAIN (ANALYZE, BUFFERS)` on top 5 chats queries in production-like data.

## What to measure in production
- Redis ops/sec per command (`SMEMBERS`, `SSCAN`, `EXISTS`, `SADD`, `SETEX`, `XADD`).
- p95/p99 latency for `send message`, `get messages`, `mark read`.
- Broker publish latency and failure/retry rates.
- DB query count/request for chats endpoints and slow query logs.
- Websocket delivery lag per gateway stream.
