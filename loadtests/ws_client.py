"""Minimal websocket client for the chat gateway, gevent friendly.

Uses ``websocket-client`` (blocking sockets) which cooperates with the gevent
monkey patching Locust applies at startup.

Protocol reference: ``app/chats/routes/v1/ws.py`` and ``app/chats/schemas/ws.py``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import websocket

from loadtests.config import config

SUBPROTOCOL = "chat.v1"


class WSClosed(Exception):
    """Raised when the gateway closed the connection."""


@dataclass(slots=True)
class GatewayClient:
    token: str
    connect_timeout: float = 10.0
    recv_timeout: float = 1.0
    sock: websocket.WebSocket | None = field(default=None)
    connection_id: str | None = field(default=None)
    gateway_id: str | None = field(default=None)
    last_seq_by_chat: dict[str, int] = field(default_factory=dict)

    def connect(self) -> float:
        """Connect and wait for ``ws.ready``. Returns elapsed milliseconds."""
        started = time.perf_counter()
        self.sock = websocket.create_connection(
            config.ws_url(self.token),
            timeout=self.connect_timeout,
            subprotocols=[SUBPROTOCOL],
            enable_multithread=True,
        )
        ready = self._recv_until("ws.ready", timeout=self.connect_timeout)
        payload = ready.get("payload") or {}
        self.connection_id = payload.get("connection_id")
        self.gateway_id = payload.get("gateway_id")
        self.sock.settimeout(self.recv_timeout)
        return (time.perf_counter() - started) * 1_000.0

    def send_command(self, command: dict[str, Any]) -> None:
        if self.sock is None:
            raise WSClosed("socket is not connected")
        self.sock.send(json.dumps(command))

    def subscribe(self, chat_id: str, last_seq: int | None = None) -> None:
        payload: dict[str, Any] = {"op": "subscribe", "chat_id": str(chat_id)}
        if last_seq is not None:
            payload["last_seq"] = last_seq
        self.send_command(payload)

    def unsubscribe(self, chat_id: str) -> None:
        self.send_command({"op": "unsubscribe", "chat_id": str(chat_id)})

    def resume(self, cursors: dict[str, int]) -> None:
        self.send_command({"op": "resume", "cursors": {str(k): int(v) for k, v in cursors.items()}})

    def pong(self) -> None:
        self.send_command({"op": "pong"})

    def recv(self, timeout: float | None = None) -> dict[str, Any] | None:
        """Receive one frame. ``None`` means "nothing within the timeout"."""
        if self.sock is None:
            raise WSClosed("socket is not connected")
        if timeout is not None:
            self.sock.settimeout(timeout)
        try:
            raw = self.sock.recv()
        except websocket.WebSocketTimeoutException:
            return None
        except (
            websocket.WebSocketConnectionClosedException,
            ConnectionResetError,
            OSError,
        ) as exc:
            raise WSClosed(str(exc)) from exc

        if raw is None or raw == "":
            raise WSClosed("empty frame")
        if isinstance(raw, bytes):
            raw = raw.decode()

        event = json.loads(raw)
        # Answer server heartbeats so the connection is not reaped after
        # WS_HEARTBEAT_TIMEOUT while a reader sits idle.
        if event.get("type") == "ws.ping":
            self.pong()

        chat_id = event.get("chat_id")
        seq = event.get("seq")
        if chat_id and isinstance(seq, int):
            known = self.last_seq_by_chat.get(str(chat_id), 0)
            if seq > known:
                self.last_seq_by_chat[str(chat_id)] = seq
        return event

    def _recv_until(self, event_type: str, timeout: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            event = self.recv(timeout=max(0.05, deadline - time.monotonic()))
            if event is None:
                continue
            if event.get("type") == event_type:
                return event
        raise WSClosed(f"did not receive {event_type} within {timeout}s")

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:  # noqa: BLE001 - closing must never fail a scenario
                pass
            finally:
                self.sock = None
