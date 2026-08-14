"""Shared helpers for the Locust scenarios."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from locust.env import Environment

from loadtests.config import config
from loadtests.thresholds import Thresholds, thresholds_from

REST_SEND_NAME = "POST /chats/{chat_id}/messages/"
WS_DELIVERY_NAME = "ws.new_message delivery"
WS_CONNECT_NAME = "ws connect"
WS_SUBSCRIBE_NAME = "ws subscribe"
WS_RESUME_NAME = "ws resume"


@dataclass(slots=True)
class ChatFixture:
    chat_id: str
    chat_type: str
    fanout_strategy: str
    member_count: int
    owner_id: int
    member_ids: list[int]


@dataclass(slots=True)
class Dataset:
    users: dict[int, str]
    cohorts: dict[str, list[ChatFixture]]

    def cohort(self, name: str) -> list[ChatFixture]:
        chats = self.cohorts.get(name) or []
        if not chats:
            raise RuntimeError(
                f"cohort '{name}' is empty in {config.dataset_path}. "
                f"Re-run loadtests.seed with a non-zero count for it."
            )
        return chats

    def username(self, user_id: int) -> str:
        return self.users.get(user_id, f"lt_user_{user_id}")


_dataset: Dataset | None = None


def load_dataset(path: str | None = None) -> Dataset:
    global _dataset  # noqa: PLW0603
    if _dataset is not None:
        return _dataset

    dataset_path = Path(path or config.dataset_path)
    if not dataset_path.exists():
        raise RuntimeError(
            f"dataset not found at {dataset_path}. Run `python -m loadtests.seed` first."
        )

    raw = json.loads(dataset_path.read_text())
    _dataset = Dataset(
        users={int(k): v for k, v in raw["users"].items()},
        cohorts={
            name: [ChatFixture(**item) for item in items]
            for name, items in raw["cohorts"].items()
        },
    )
    return _dataset


class DeliverySamples:
    """Collects end-to-end delivery latencies observed by websocket readers."""

    def __init__(self) -> None:
        self._samples_ms: list[float] = []
        self._by_strategy: dict[str, list[float]] = {}

    def add(self, latency_ms: float, fanout_strategy: str) -> None:
        self._samples_ms.append(latency_ms)
        self._by_strategy.setdefault(fanout_strategy, []).append(latency_ms)

    def __len__(self) -> int:
        return len(self._samples_ms)

    def percentile(self, ratio: float, fanout_strategy: str | None = None) -> float:
        samples = (
            self._by_strategy.get(fanout_strategy, [])
            if fanout_strategy
            else self._samples_ms
        )
        if not samples:
            return 0.0
        ordered = sorted(samples)
        index = min(len(ordered) - 1, max(0, int(round(ratio * len(ordered))) - 1))
        return ordered[index]

    def summary(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "samples": len(self._samples_ms),
            "p50_ms": round(self.percentile(0.50), 2),
            "p95_ms": round(self.percentile(0.95), 2),
            "p99_ms": round(self.percentile(0.99), 2),
            "max_ms": round(max(self._samples_ms), 2) if self._samples_ms else 0.0,
            "by_fanout_strategy": {},
        }
        for strategy, samples in self._by_strategy.items():
            result["by_fanout_strategy"][strategy] = {
                "samples": len(samples),
                "p50_ms": round(self.percentile(0.50, strategy), 2),
                "p95_ms": round(self.percentile(0.95, strategy), 2),
                "p99_ms": round(self.percentile(0.99, strategy), 2),
            }
        return result


delivery_samples = DeliverySamples()


def _stats_for(environment: Environment, name: str) -> Any:
    for (entry_name, _method), entry in environment.stats.entries.items():
        if entry_name == name:
            return entry
    return None


def check_acceptance(environment: Environment, *, require_delivery: bool) -> list[str]:
    """Evaluate acceptance criteria. Returns a list of violations."""
    limits: Thresholds = thresholds_from(environment)
    violations: list[str] = []

    rest = _stats_for(environment, REST_SEND_NAME)
    if rest is not None and rest.num_requests:
        error_rate = rest.num_failures / rest.num_requests
        if error_rate > limits.rest_error_rate:
            violations.append(
                f"REST send error rate {error_rate:.4f} > {limits.rest_error_rate:.4f}"
            )
        p95 = rest.get_response_time_percentile(0.95) or 0
        p99 = rest.get_response_time_percentile(0.99) or 0
        if p95 > limits.rest_p95_ms:
            violations.append(f"REST send p95 {p95:.0f}ms > {limits.rest_p95_ms:.0f}ms")
        if p99 > limits.rest_p99_ms:
            violations.append(f"REST send p99 {p99:.0f}ms > {limits.rest_p99_ms:.0f}ms")

    ws_failures = 0
    ws_requests = 0
    for name in (WS_CONNECT_NAME, WS_SUBSCRIBE_NAME, WS_RESUME_NAME):
        entry = _stats_for(environment, name)
        if entry is not None:
            ws_failures += entry.num_failures
            ws_requests += entry.num_requests
    if ws_requests:
        ws_error_rate = ws_failures / ws_requests
        if ws_error_rate > limits.ws_connect_error_rate:
            violations.append(
                f"WS connect/subscribe/resume error rate {ws_error_rate:.4f} "
                f"> {limits.ws_connect_error_rate:.4f}"
            )

    if require_delivery:
        if len(delivery_samples) < limits.min_delivery_samples:
            violations.append(
                f"only {len(delivery_samples)} delivery samples collected, "
                f"need >= {limits.min_delivery_samples}; the run is not conclusive"
            )
        else:
            p95 = delivery_samples.percentile(0.95)
            p99 = delivery_samples.percentile(0.99)
            if p95 > limits.delivery_p95_ms:
                violations.append(
                    f"delivery p95 {p95:.0f}ms > {limits.delivery_p95_ms:.0f}ms"
                )
            if p99 > limits.delivery_p99_ms:
                violations.append(
                    f"delivery p99 {p99:.0f}ms > {limits.delivery_p99_ms:.0f}ms"
                )
            # Per-strategy check: fanout_on_write is the one called out in the
            # acceptance criteria, and a healthy active_subscribers average can
            # otherwise hide a bad fanout_on_write tail.
            fow_p95 = delivery_samples.percentile(0.95, "fanout_on_write")
            if fow_p95 > limits.delivery_p95_ms:
                violations.append(
                    f"fanout_on_write delivery p95 {fow_p95:.0f}ms "
                    f"> {limits.delivery_p95_ms:.0f}ms"
                )

    return violations


def report_and_fail(environment: Environment, *, require_delivery: bool) -> None:
    """Print the summary and set a non-zero process exit code on violation."""
    if delivery_samples:
        print("\n=== delivery latency (end-to-end, client observed) ===")
        print(json.dumps(delivery_samples.summary(), indent=2))

    violations = check_acceptance(environment, require_delivery=require_delivery)
    if violations:
        print("\n=== ACCEPTANCE FAILED ===")
        for item in violations:
            print(f"  - {item}")
        environment.process_exit_code = 1
    else:
        print("\n=== acceptance criteria met ===")


def monotonic_ms() -> float:
    return time.monotonic() * 1_000.0
