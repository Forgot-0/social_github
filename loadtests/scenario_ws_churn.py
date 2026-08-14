"""Scenario (c): websocket connection churn and resume.

Repeatedly closes and reopens connections, re-subscribes, and issues ``resume``
with a per-chat cursor. The question being answered: do the delivery router and
redis degrade when connections re-subscribe often (route SADD/SREM churn,
``ws:sub:chat:*`` set rewrites, gateway stream re-registration)?

Rate limiting on websocket commands does not exist yet in ``app/chats/routes/
v1/ws.py`` (no limiter on the RESUME/SUBSCRIBE branches). When it lands, this
scenario must stay under the limit, otherwise it measures RATE_LIMITED replies
instead of throughput. That is why the resume interval is a parameter:

    LT_WS_RESUME_INTERVAL_SECONDS=1.0   # >= 1 / limit_per_second
    LT_WS_CHURN_HOLD_SECONDS=5.0        # how long a connection is kept open

Any ``ws.error`` frame with code RATE_LIMITED is counted as a failure and named
separately, so a run that accidentally exceeds the limit is obvious in the stats
table rather than silently deflating the numbers.

Run:
    locust -f loadtests/scenario_ws_churn.py --headless -u 200 -r 20 -t 3m
"""

from __future__ import annotations

import random
import time

from locust import User, constant, events, task
from locust.env import Environment

from loadtests.common import (
    WS_CONNECT_NAME,
    WS_RESUME_NAME,
    WS_SUBSCRIBE_NAME,
    load_dataset,
    report_and_fail,
)
from loadtests.config import config
from loadtests.tokens import mint_access_token
from loadtests.ws_client import GatewayClient, WSClosed

WS_RATE_LIMITED_NAME = "ws RATE_LIMITED"
_slot = 0


def _next_slot() -> int:
    global _slot  # noqa: PLW0603
    slot = _slot
    _slot += 1
    return slot


class ChurnUser(User):
    """Connect, subscribe, resume a few times, disconnect, repeat."""

    wait_time = constant(0)

    def on_start(self) -> None:
        dataset = load_dataset()
        cohort = dataset.cohort(config.target_cohort)
        self.chat = cohort[_next_slot() % len(cohort)]
        members = [uid for uid in self.chat.member_ids if uid != self.chat.owner_id]
        self.user_id = random.choice(members or self.chat.member_ids)
        self.username = dataset.username(self.user_id)
        self.cursor = 0

    def _fire(self, name: str, started: float, exception: BaseException | None = None) -> None:
        self.environment.events.request.fire(
            request_type="WS",
            name=name,
            response_time=(time.perf_counter() - started) * 1_000.0,
            response_length=0,
            exception=exception,
        )

    def _drain(self, client: GatewayClient, seconds: float) -> None:
        """Read frames for a while, surfacing RATE_LIMITED errors."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            event = client.recv(timeout=min(0.5, max(0.05, deadline - time.monotonic())))
            if event is None:
                continue
            if event.get("type") == "ws.error" and event.get("code") == "RATE_LIMITED":
                self.environment.events.request.fire(
                    request_type="WS",
                    name=WS_RATE_LIMITED_NAME,
                    response_time=0,
                    response_length=0,
                    exception=RuntimeError(
                        "gateway rate limited a ws command; raise "
                        "LT_WS_RESUME_INTERVAL_SECONDS or this run measures throttling"
                    ),
                )
            chat_id = str(event.get("chat_id") or "")
            if chat_id == self.chat.chat_id:
                self.cursor = max(self.cursor, client.last_seq_by_chat.get(chat_id, 0))

    @task
    def churn(self) -> None:
        # Token is re-minted per cycle: a real reconnect carries a fresh token
        # and this keeps long runs from expiring mid-flight.
        client = GatewayClient(token=mint_access_token(self.user_id, self.username))

        started = time.perf_counter()
        try:
            client.connect()
        except Exception as exc:  # noqa: BLE001
            self._fire(WS_CONNECT_NAME, started, exc)
            time.sleep(config.ws_resume_interval_seconds)
            return
        self._fire(WS_CONNECT_NAME, started)

        try:
            started = time.perf_counter()
            client.subscribe(self.chat.chat_id, last_seq=self.cursor or None)
            self._fire(WS_SUBSCRIBE_NAME, started)

            hold = config.ws_churn_hold_seconds
            interval = max(0.01, config.ws_resume_interval_seconds)
            resumes = max(1, int(hold / interval))

            for _ in range(resumes):
                self._drain(client, interval)
                started = time.perf_counter()
                client.resume({self.chat.chat_id: self.cursor})
                self._fire(WS_RESUME_NAME, started)

            self._drain(client, interval)
        except WSClosed as exc:
            self._fire(WS_CONNECT_NAME, started, exc)
        finally:
            client.close()


@events.quitting.add_listener
def _acceptance(environment: Environment, **_kwargs) -> None:
    # No writer in this scenario, so there is no delivery latency to assert on.
    report_and_fail(environment, require_delivery=False)
