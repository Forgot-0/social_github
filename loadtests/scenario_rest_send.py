"""Scenario (a): REST throughput of message sending.

Measures msg/sec and p95/p99 of the POST /messages/ response only. Delivery
latency is a separate scenario (scenario_ws_fanout.py) on purpose: mixing them
into one number hides which side is slow.

Run:
    locust -f loadtests/scenario_rest_send.py --headless \\
        -u 100 -r 20 -t 3m --host http://app:8000

Notes on correctness of the numbers:
  * Idempotency-Key is unique per attempt (uuid4 per task call). Reusing a key
    across retries would measure redis idempotency cache hits, not writes.
  * chat_config.RATE_LIMIT_MESSAGES_PER_SECOND (10/s per user) applies to
    POST /messages/. Push a single user harder than that and you measure 429s.
    Scale users, not per-user rate: keep LT_SEND_WAIT_MIN_SECONDS >= 0.1.
"""

from __future__ import annotations

import random
import string
from uuid import uuid4

from locust import HttpUser, between, events, task
from locust.env import Environment

from loadtests.common import (
    REST_SEND_NAME,
    load_dataset,
    report_and_fail,
)
from loadtests.config import config
from loadtests.tokens import mint_access_token

_ALPHABET = string.ascii_letters + string.digits


def _body(size_bytes: int) -> str:
    return "".join(random.choices(_ALPHABET, k=max(1, size_bytes)))


class RestSendUser(HttpUser):
    """Sends messages into a chat the user is actually a member of."""

    wait_time = between(config.send_wait_min_seconds, config.send_wait_max_seconds)
    host = config.api_base_url

    def on_start(self) -> None:
        dataset = load_dataset()
        cohort = dataset.cohort(config.target_cohort)
        self.chat = random.choice(cohort)

        # Channels only accept messages from editors and above; the seeded owner
        # is the only such member, so pick the owner there.
        if self.chat.chat_type == "channel":
            self.user_id = self.chat.owner_id
        else:
            self.user_id = random.choice(self.chat.member_ids)

        self.token = mint_access_token(self.user_id, dataset.username(self.user_id))
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        self.url = config.messages_url(self.chat.chat_id)

    @task
    def send_message(self) -> None:
        with self.client.post(
            self.url,
            json={"content": _body(config.message_size_bytes), "message_type": "text"},
            headers={"Idempotency-Key": str(uuid4())},
            name=REST_SEND_NAME,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 429:
                # Counted as a failure on purpose: hitting the per-user limit
                # means the load shape is wrong, not that the server is slow.
                response.failure("429 rate limited (reduce per-user rate)")
            else:
                response.failure(f"unexpected status {response.status_code}: {response.text[:200]}")


@events.quitting.add_listener
def _acceptance(environment: Environment, **_kwargs) -> None:
    report_and_fail(environment, require_delivery=False)
