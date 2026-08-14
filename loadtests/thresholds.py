"""Acceptance criteria as code.

Thresholds are parameters, never constants baked into a scenario. Resolution
order: Locust CLI flag > environment variable > the placeholder defaults below.

The defaults are deliberately loose placeholders. No baseline has been captured
yet, so guessing tight numbers would only produce meaningless red builds. After
the first run, set real values in ``loadtests/thresholds.env`` and reference
them from CI.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from locust import events
from locust.env import Environment


def _f(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw else default


@dataclass(slots=True)
class Thresholds:
    """Placeholder values — replace after the first baseline run."""

    rest_p95_ms: float = 0.0
    rest_p99_ms: float = 0.0
    rest_error_rate: float = 0.0
    delivery_p95_ms: float = 0.0
    delivery_p99_ms: float = 0.0
    ws_connect_error_rate: float = 0.0
    min_delivery_samples: int = 0


@events.init_command_line_parser.add_listener
def _add_threshold_args(parser) -> None:  # noqa: ANN001
    group = parser.add_argument_group("acceptance thresholds")
    group.add_argument(
        "--rest-p95-ms",
        type=float,
        env_var="LT_REST_P95_MS",
        default=_f("LT_REST_P95_MS", 500.0),
        help="Max allowed p95 of POST /messages/ response time, ms",
    )
    group.add_argument(
        "--rest-p99-ms",
        type=float,
        env_var="LT_REST_P99_MS",
        default=_f("LT_REST_P99_MS", 1_500.0),
        help="Max allowed p99 of POST /messages/ response time, ms",
    )
    group.add_argument(
        "--rest-error-rate",
        type=float,
        env_var="LT_REST_ERROR_RATE",
        default=_f("LT_REST_ERROR_RATE", 0.01),
        help="Max allowed failure ratio for REST send (0.01 = 1%%)",
    )
    group.add_argument(
        "--delivery-p95-ms",
        type=float,
        env_var="LT_DELIVERY_P95_MS",
        default=_f("LT_DELIVERY_P95_MS", 2_000.0),
        help="Max allowed p95 end-to-end WS delivery latency, ms",
    )
    group.add_argument(
        "--delivery-p99-ms",
        type=float,
        env_var="LT_DELIVERY_P99_MS",
        default=_f("LT_DELIVERY_P99_MS", 5_000.0),
        help="Max allowed p99 end-to-end WS delivery latency, ms",
    )
    group.add_argument(
        "--ws-connect-error-rate",
        type=float,
        env_var="LT_WS_CONNECT_ERROR_RATE",
        default=_f("LT_WS_CONNECT_ERROR_RATE", 0.02),
        help="Max allowed failure ratio for ws connect/subscribe/resume",
    )
    group.add_argument(
        "--min-delivery-samples",
        type=int,
        env_var="LT_MIN_DELIVERY_SAMPLES",
        default=int(_f("LT_MIN_DELIVERY_SAMPLES", 100)),
        help="Fail the run if fewer delivery samples were collected",
    )


def thresholds_from(environment: Environment) -> Thresholds:
    opts = environment.parsed_options
    return Thresholds(
        rest_p95_ms=getattr(opts, "rest_p95_ms", 500.0),
        rest_p99_ms=getattr(opts, "rest_p99_ms", 1_500.0),
        rest_error_rate=getattr(opts, "rest_error_rate", 0.01),
        delivery_p95_ms=getattr(opts, "delivery_p95_ms", 2_000.0),
        delivery_p99_ms=getattr(opts, "delivery_p99_ms", 5_000.0),
        ws_connect_error_rate=getattr(opts, "ws_connect_error_rate", 0.02),
        min_delivery_samples=getattr(opts, "min_delivery_samples", 100),
    )
