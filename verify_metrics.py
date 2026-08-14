"""Verify the gateway metrics wiring without a real WS/redis stack."""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from prometheus_client import REGISTRY

from app.chats.dtos.delivery import ORIGIN_TS_FIELD
from app.chats.services.ws import ChatConnectionManager


class FakeRedis:
    def __init__(self):
        self.stream_len = 4242
        self.pending = {"pending": 7}

    def pipeline(self, transaction=False):
        return self

    def __getattr__(self, name):
        def noop(*a, **k):
            return self
        return noop

    async def execute(self):
        return []

    async def xlen(self, key):
        return self.stream_len

    async def xpending(self, key, group):
        return self.pending

    async def smembers(self, key):
        return set()


@dataclass
class FakeConn:
    connection_id: str
    user_id: int
    device_id: str = "d"
    gateway_id: str = "gw-test"
    subscriptions: set = field(default_factory=set)
    closed: bool = False
    connected_at: Any = field(default_factory=lambda: __import__("app.core.utils", fromlist=["now_utc"]).now_utc())
    sent: list = field(default_factory=list)
    accept_sends: bool = True

    async def start(self):
        pass

    async def close(self, code=1000, reason=""):
        self.closed = True

    def try_send(self, event):
        if not self.accept_sends:
            return False
        self.sent.append(dict(event))
        return True


def sample(name, labels):
    return REGISTRY.get_sample_value(name, labels)


async def main():
    mgr = ChatConnectionManager(redis=FakeRedis(), gateway_id="gw-test")
    gw = {"gateway_id": "gw-test"}

    c1 = FakeConn("c1", 1)
    c2 = FakeConn("c2", 2)
    await mgr.register(c1)
    await mgr.register(c2)
    print("after 2 registers: conns=%s users=%s" % (
        sample("chat_ws_active_connections", gw), sample("chat_ws_active_users", gw)))
    assert sample("chat_ws_active_connections", gw) == 2
    assert sample("chat_ws_active_users", gw) == 2

    await mgr.subscribe_chat(c1, "chatA")
    await mgr.subscribe_chat(c2, "chatA")
    print("after subscribe both to chatA: chats=%s" % sample("chat_ws_subscribed_chats", gw))
    assert sample("chat_ws_subscribed_chats", gw) == 1

    # Delivery latency: origin 0.5s in the past, one event to two connections.
    origin = time.time() - 0.5
    event = {
        "type": "new_message",
        "chat_id": "chatA",
        "fanout_strategy": "fanout_on_write",
        ORIGIN_TS_FIELD: origin,
    }
    await mgr.send_to_chat_local("chatA", event)
    labels = {"fanout_strategy": "fanout_on_write", "event_type": "new_message"}
    cnt = sample("chat_ws_delivery_latency_seconds_count", labels)
    total = sample("chat_ws_delivery_latency_seconds_sum", labels)
    print("delivery observations=%s sum=%.3fs (expect 2 obs, ~1.0s total)" % (cnt, total))
    assert cnt == 2, cnt
    assert 0.8 < total < 1.6, total
    assert len(c1.sent) == 1 and len(c2.sent) == 1
    print("origin_ts survived into frame:", ORIGIN_TS_FIELD in c1.sent[0])
    assert ORIGIN_TS_FIELD in c1.sent[0]

    # Event without origin_ts must not observe or crash.
    await mgr.send_to_chat_local("chatA", {"type": "new_message", "chat_id": "chatA"})
    assert sample("chat_ws_delivery_latency_seconds_count", labels) == 2

    # Slow consumer -> dropped frame counter.
    c2.accept_sends = False
    await mgr.send_to_chat_local("chatA", {"type": "new_message", "chat_id": "chatA",
                                          "fanout_strategy": "fanout_on_write",
                                          ORIGIN_TS_FIELD: time.time()})
    await asyncio.sleep(0.05)
    print("frames dropped:", sample("chat_ws_frames_dropped_total", gw))
    assert sample("chat_ws_frames_dropped_total", gw) == 1

    # Backlog loop: one iteration.
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
    print("\nALL METRIC ASSERTIONS PASSED")


asyncio.run(main())
