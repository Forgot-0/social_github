#!/bin/bash

# Script to apply websocket metrics patches
# Location: ~/social_github/apply_metrics_patches.sh
# Usage: cd ~/social_github && bash apply_metrics_patches.sh

set -e

echo "🚀 Starting WebSocket metrics patch application..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if required files exist
check_file() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}❌ File not found: $1${NC}"
        exit 1
    fi
}

check_file "app/chats/services/ws.py"
check_file "app/chats/services/delivery_router.py"
check_file "app/consumers.py"
check_file "loadtests/seed.py"
check_file "loadtests/scenario_ws_fanout.py"
check_file "verify_metrics.py"

echo -e "${YELLOW}✓ All required files found${NC}"
echo ""

# Patch 1: Update ws.py imports and add startup task
echo "📝 [1/6] Patching ws.py imports and startup tasks..."
python3 << 'EOF'
import re, pathlib
p = pathlib.Path('app/chats/services/ws.py')
s = p.read_text()

# 1. imports
s = s.replace(
"""import asyncio
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import orjson
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.chats.config import chat_config
from app.chats.dtos.websocket import WSConnection
from app.chats.keys import WebsocketKeys
from app.core.utils import now_utc""",
"""import asyncio
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import orjson
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.chats.config import chat_config
from app.chats.dtos.delivery import ORIGIN_TS_FIELD
from app.chats.dtos.websocket import WSConnection
from app.chats.keys import WebsocketKeys
from app.chats.metrics import (
    WS_ACTIVE_CONNECTIONS,
    WS_ACTIVE_USERS,
    WS_DELIVERY_LATENCY,
    WS_FRAMES_DROPPED,
    WS_GATEWAY_STREAM_BACKLOG,
    WS_GATEWAY_STREAM_PENDING,
    WS_SUBSCRIBED_CHATS,
)
from app.core.utils import now_utc""")

# 2. startup tasks: add backlog loop
s = s.replace(
"""            asyncio.create_task(self._consume_gateway_stream_loop(), name=f"ws:stream:{self.gateway_id}"),
        ]""",
"""            asyncio.create_task(self._consume_gateway_stream_loop(), name=f"ws:stream:{self.gateway_id}"),
            asyncio.create_task(self._refresh_stream_backlog_loop(), name=f"ws:backlog:{self.gateway_id}"),
        ]""")
p.write_text(s)
print("✓ Imports and startup tasks patched")
EOF

# Patch 2: Add gauge sync methods
echo -e "${GREEN}✓${NC} Patch 1 complete"
echo "📝 [2/6] Adding gauge sync methods..."
python3 << 'EOF'
import pathlib
p = pathlib.Path('app/chats/services/ws.py')
s = p.read_text()

# 3. gauge refresh helper + call it from register/unregister/subscribe/unsubscribe
s = s.replace(
"""        await self.set_route_users(conn)
        await conn.start()

        for stale in stale_to_close:""",
"""        await self.set_route_users(conn)
        await conn.start()
        self._sync_connection_gauges()

        for stale in stale_to_close:""")

s = s.replace(
"""        await conn.close(code=close_code, reason=close_reason)

        logger.info(
            "WebSocket unregistered",""",
"""        await conn.close(code=close_code, reason=close_reason)
        self._sync_connection_gauges()

        logger.info(
            "WebSocket unregistered",""")

# subscribe_chat / unsubscribe_chat gauge sync (subscribed chats count)
s = s.replace(
"""            WebsocketKeys.connection_subscription_key(conn.connection_id, chat_id),
            chat_config.WS_ACTIVE_SUBSCRIPTION_TTL,
            route,
        )
        await pipe.execute()

    async def unsubscribe_chat(self, conn: WSConnection, chat_id: str) -> None:""",
"""            WebsocketKeys.connection_subscription_key(conn.connection_id, chat_id),
            chat_config.WS_ACTIVE_SUBSCRIPTION_TTL,
            route,
        )
        await pipe.execute()
        self._sync_connection_gauges()

    async def unsubscribe_chat(self, conn: WSConnection, chat_id: str) -> None:""")

s = s.replace(
"""        if remove_gateway_route:
            pipe.srem(WebsocketKeys.active_subscription_gateways_key(chat_id), self.gateway_id)
        await pipe.execute()""",
"""        if remove_gateway_route:
            pipe.srem(WebsocketKeys.active_subscription_gateways_key(chat_id), self.gateway_id)
        await pipe.execute()
        self._sync_connection_gauges()""")
p.write_text(s)
print("✓ Gauge sync methods added")
EOF

# Patch 3: Add send metrics and frames dropped counter
echo -e "${GREEN}✓${NC} Patch 2 complete"
echo "📝 [3/6] Adding send metrics and frame drop counter..."
python3 << 'EOF'
import pathlib
p = pathlib.Path('app/chats/services/ws.py')
s = p.read_text()

old_send = """    async def _send_to_connections(self, conns: list[WSConnection], event: dict[str, Any]) -> None:
        if not conns:
            return
        for start in range(0, len(conns), _LOCAL_SEND_BATCH_SIZE):
            batch = conns[start:start + _LOCAL_SEND_BATCH_SIZE]
            await asyncio.gather(
                *(self._send_or_unregister(conn, event) for conn in batch),
                return_exceptions=False,
            )"""
new_send = """    async def _send_to_connections(self, conns: list[WSConnection], event: dict[str, Any]) -> None:
        if not conns:
            return

        origin_ts = event.get(ORIGIN_TS_FIELD)
        latency_metric = None
        if isinstance(origin_ts, int | float):
            latency_metric = WS_DELIVERY_LATENCY.labels(
                fanout_strategy=str(event.get("fanout_strategy") or "unknown"),
                event_type=str(event.get("type") or "unknown"),
            )

        for start in range(0, len(conns), _LOCAL_SEND_BATCH_SIZE):
            batch = conns[start:start + _LOCAL_SEND_BATCH_SIZE]
            await asyncio.gather(
                *(self._send_or_unregister(conn, event) for conn in batch),
                return_exceptions=False,
            )
            if latency_metric is not None:
                # One observation per frame; the batch shares a single clock read
                # so a 200k member fanout does not pay for 200k time() calls.
                elapsed = max(0.0, time.time() - float(origin_ts))
                for _ in batch:
                    latency_metric.observe(elapsed)"""
assert old_send in s
s = s.replace(old_send, new_send)

old_drop = """        logger.warning(
            "Dropping slow WebSocket consumer",
            extra={"connection_id": conn.connection_id, "user_id": conn.user_id},
        )"""
new_drop = """        WS_FRAMES_DROPPED.labels(gateway_id=self.gateway_id).inc()
        logger.warning(
            "Dropping slow WebSocket consumer",
            extra={"connection_id": conn.connection_id, "user_id": conn.user_id},
        )"""
assert old_drop in s
s = s.replace(old_drop, new_drop)
p.write_text(s)
print("✓ Send metrics and frame drop counter added")
EOF

# Patch 4: Add helper methods at end of class
echo -e "${GREEN}✓${NC} Patch 3 complete"
echo "📝 [4/6] Adding helper methods (_sync_connection_gauges, _refresh_stream_backlog_loop)..."
python3 << 'EOF'
import pathlib
p = pathlib.Path('app/chats/services/ws.py')
s = p.read_text()
tail_old = """    def _unsubscribe_chat_in_memory(self, conn: WSConnection, chat_id: str) -> None:
        conn.subscriptions.discard(chat_id)"""
tail_new = '''    def _sync_connection_gauges(self) -> None:
        """Export the in-memory registries as gauges.

        Cheap: three ``len()`` calls, no locking. Called from register/unregister
        and (un)subscribe_chat, which are the only places these dicts change size.
        """
        WS_ACTIVE_CONNECTIONS.labels(gateway_id=self.gateway_id).set(len(self.connections_by_id))
        WS_ACTIVE_USERS.labels(gateway_id=self.gateway_id).set(len(self.connections_by_user))
        WS_SUBSCRIBED_CHATS.labels(gateway_id=self.gateway_id).set(len(self.subscriptions_by_chat))

    async def _refresh_stream_backlog_loop(self) -> None:
        """Periodically export XLEN/XPENDING of this gateway's redis stream.

        Same shape as ``_refresh_routes_loop``: single task on the manager, no
        separate service.
        """
        interval = float(chat_config.WS_GATEWAY_STREAM_BACKLOG_INTERVAL)
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=interval)
                break
            except TimeoutError:
                pass

            try:
                backlog = await self.redis.xlen(self.stream_key)
                WS_GATEWAY_STREAM_BACKLOG.labels(gateway_id=self.gateway_id).set(backlog)

                pending = 0
                try:
                    summary = await self.redis.xpending(self.stream_key, self.stream_group)
                except ResponseError:
                    summary = None
                if summary:
                    pending = int(summary.get("pending", 0) or 0)
                WS_GATEWAY_STREAM_PENDING.labels(gateway_id=self.gateway_id).set(pending)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Failed to refresh websocket gateway stream backlog",
                    extra={"gateway_id": self.gateway_id},
                )

    def _unsubscribe_chat_in_memory(self, conn: WSConnection, chat_id: str) -> None:
        conn.subscriptions.discard(chat_id)'''
assert tail_old in s
s = s.replace(tail_old, tail_new)
p.write_text(s)
print("✓ Helper methods added")
EOF

# Patch 5: Update delivery_router.py
echo -e "${GREEN}✓${NC} Patch 4 complete"
echo "📝 [5/6] Patching delivery_router.py imports and enqueue logic..."
python3 << 'EOF'
import pathlib
dr = pathlib.Path('app/chats/services/delivery_router.py')
s = dr.read_text()

s = s.replace(
"""from app.chats.config import chat_config
from app.chats.dtos.delivery import build_ws_event, chunks, is_chat_domain_event
from app.chats.keys import WebsocketKeys
from app.chats.models.chat import ChatFanoutStrategy""",
"""from app.chats.config import chat_config
from app.chats.dtos.delivery import ORIGIN_TS_FIELD, build_ws_event, chunks, is_chat_domain_event
from app.chats.keys import WebsocketKeys
from app.chats.metrics import get_delivery_router_metrics
from app.chats.models.chat import ChatFanoutStrategy""")

s = s.replace("""import orjson
from redis.asyncio import Redis""", """import orjson
import time
from redis.asyncio import Redis""")

old = """        ts = ws_event.get("ts") or now_utc().isoformat()
        pipe = self.redis.pipeline(transaction=False)
        enqueued = 0

        for gateway_id, user_ids in routes_by_gateway.items():"""
new = """        ts = ws_event.get("ts") or now_utc().isoformat()
        pipe = self.redis.pipeline(transaction=False)
        enqueued = 0
        recipients = 0

        for gateway_id, user_ids in routes_by_gateway.items():"""
assert old in s
s = s.replace(old, new)

old2 = """                    approximate=True,
                )
                enqueued += 1

        if not enqueued:
            return

        try:
            await pipe.execute()
        except Exception:
            logger.exception(
                "Failed to enqueue websocket gateway deliveries",
                extra={"gateways": list(routes_by_gateway), "enqueued": enqueued},
            )
            raise"""
new2 = """                    approximate=True,
                )
                enqueued += 1
                recipients += len(user_chunk)

        if not enqueued:
            return

        try:
            await pipe.execute()
        except Exception:
            logger.exception(
                "Failed to enqueue websocket gateway deliveries",
                extra={"gateways": list(routes_by_gateway), "enqueued": enqueued},
            )
            raise

        self._observe_enqueue(ws_event, enqueued=enqueued, recipients=recipients)

    @staticmethod
    def _observe_enqueue(ws_event: dict[str, Any], *, enqueued: int, recipients: int) -> None:
        metrics = get_delivery_router_metrics()
        if metrics is None:
            return

        strategy = str(ws_event.get("fanout_strategy") or "unknown")
        metrics.stream_entries.labels(fanout_strategy=strategy).inc(enqueued)
        metrics.recipients.labels(fanout_strategy=strategy).inc(recipients)

        origin_ts = ws_event.get(ORIGIN_TS_FIELD)
        if isinstance(origin_ts, int | float):
            metrics.enqueue_latency.labels(fanout_strategy=strategy).observe(
                max(0.0, time.time() - float(origin_ts))
            )"""
assert old2 in s
s = s.replace(old2, new2)
dr.write_text(s)
print("✓ delivery_router.py patched")
EOF

# Patch 6: Update consumers.py
echo -e "${GREEN}✓${NC} Patch 5 complete"
echo "📝 [6/6] Patching consumers.py for metrics registration..."
python3 << 'EOF'
import pathlib
c = pathlib.Path('app/consumers.py')
s = c.read_text()
s = s.replace(
"""from app.chats.consumers import delivery, profiles
from app.core.configs.app import app_config""",
"""from app.chats.consumers import delivery, profiles
from app.chats.metrics import register_delivery_router_metrics, set_delivery_router_metrics
from app.core.configs.app import app_config""")
s = s.replace(
"""    configure_logging()
    registry = CollectorRegistry()
    log = structlog.get_logger("main")""",
"""    configure_logging()
    registry = CollectorRegistry()
    set_delivery_router_metrics(register_delivery_router_metrics(registry))
    log = structlog.get_logger("main")""")
c.write_text(s)
print("✓ consumers.py patched")
EOF

# Patch 7: Clean up loadtests/seed.py
echo -e "${GREEN}✓${NC} Patch 6 complete"
echo "📝 [7/9] Cleaning up loadtests/seed.py..."
python3 << 'EOF'
import pathlib
p = pathlib.Path('loadtests/seed.py')
s = p.read_text()
s = s.replace("""from uuid import UUID, uuid7""", """from uuid import uuid7""")
s = s.replace("""

# Referenced so linters keep the import that documents where chat ids come from.
_ = UUID

""", "")
s = s.replace("""                dataset.direct.append(fixture)
                if len(member_rows) >= INSERT_CHUNK:
                    await flush(conn, chat_rows, member_rows)
                    chat_rows, member_rows = [], []
                del i

""", """                dataset.direct.append(fixture)
                if len(member_rows) >= INSERT_CHUNK:
                    await flush(conn, chat_rows, member_rows)
                    chat_rows, member_rows = [], []
""")
s = s.replace("""            for i in range(args.direct_chats):""", """            for _ in range(args.direct_chats):""")
p.write_text(s)
print("✓ loadtests/seed.py cleaned up")
EOF

# Patch 8: Update scenario_ws_fanout.py
echo -e "${GREEN}✓${NC} Patch 7 complete"
echo "📝 [8/9] Updating loadtests/scenario_ws_fanout.py..."
python3 << 'EOF'
import pathlib
p = pathlib.Path('loadtests/scenario_ws_fanout.py')
s = p.read_text()
s = s.replace(
"""from locust import HttpUser, User, between, constant, events, task
from locust.env import Environment""",
"""from locust import HttpUser, User, between, constant, events, task
from locust.env import Environment
from locust.exception import StopUser""")
s = s.replace(
"""            raise self.environment.runner.greenlet.GreenletExit if False else exc

""",
"""            raise StopUser from exc
""")
p.write_text(s)
print("✓ scenario_ws_fanout.py updated")
EOF

# Patch 9: Update verify_metrics.py
echo -e "${GREEN}✓${NC} Patch 8 complete"
echo "📝 [9/9] Updating verify_metrics.py..."
python3 << 'EOF'
import pathlib
p = pathlib.Path('verify_metrics.py')
s = p.read_text()
s = s.replace("""    # Backlog loop: one iteration.
    task = asyncio.create_task(mgr._refresh_stream_backlog_loop())
    await asyncio.sleep(0.1)
    mgr._shutdown_event.set()
    await asyncio.sleep(0.05)
    task.cancel()
    print("backlog=%s pending=%s" % (
        sample("chat_ws_gateway_stream_backlog", gw), sample("chat_ws_gateway_stream_pending", gw)))

    mgr._shutdown_event.clear()
    await mgr.unregister(c1)
    print("after unregister c1: conns=%s users=%s" % (
        sample("chat_ws_active_connections", gw), sample("chat_ws_active_users", gw)))
    assert sample("chat_ws_active_connections", gw) == 1
    print("\\nALL METRIC ASSERTIONS PASSED")""",
"""    # c2 was evicted by the slow-consumer path above; confirm that happened.
    print("after slow-consumer eviction: conns=%s" % sample("chat_ws_active_connections", gw))
    assert sample("chat_ws_active_connections", gw) == 1
    assert c2.closed

    # Backlog loop: it waits one interval before sampling (same shape as
    # _refresh_routes_loop), so shorten the interval for the test.
    chat_config.WS_GATEWAY_STREAM_BACKLOG_INTERVAL = 1
    task = asyncio.create_task(mgr._refresh_stream_backlog_loop())
    await asyncio.sleep(1.3)
    backlog = sample("chat_ws_gateway_stream_backlog", gw)
    pending = sample("chat_ws_gateway_stream_pending", gw)
    print("backlog=%s pending=%s (expect 4242 / 7)" % (backlog, pending))
    assert backlog == 4242, backlog
    assert pending == 7, pending
    mgr._shutdown_event.set()
    await asyncio.sleep(0.05)
    task.cancel()

    mgr._shutdown_event.clear()
    await mgr.unregister(c1)
    print("after unregister c1: conns=%s users=%s" % (
        sample("chat_ws_active_connections", gw), sample("chat_ws_active_users", gw)))
    assert sample("chat_ws_active_connections", gw) == 0
    print("\\nALL METRIC ASSERTIONS PASSED")""")
s = s.replace("""from app.chats.dtos.delivery import ORIGIN_TS_FIELD""",
"""from app.chats.config import chat_config
from app.chats.dtos.delivery import ORIGIN_TS_FIELD""")
p.write_text(s)
print("✓ verify_metrics.py updated")
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ All patches applied successfully!${NC}"
echo ""
echo "📋 Summary of changes:"
echo "  • app/chats/services/ws.py - Added metrics imports, gauge tracking, backlog loop"
echo "  • app/chats/services/delivery_router.py - Added delivery metrics tracking"
echo "  • app/consumers.py - Added metrics registration"
echo "  • loadtests/seed.py - Code cleanup (removed unused imports)"
echo "  • loadtests/scenario_ws_fanout.py - Updated StopUser exception handling"
echo "  • verify_metrics.py - Updated test assertions"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "  1. Review the changes: git diff"
echo "  2. Run tests: pytest tests/"
echo "  3. Run verification: python verify_metrics.py"
echo ""
