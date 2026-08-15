"""
Сценарий (b) из промпта: WS fanout latency.

Запуск (отдельно от остальных, п.3 промпта). K читателей = --users Locust'a,
пишущий "писатель" — ОДИН (дословно из промпта: "один 'писатель' шлёт
сообщения"), запускается не как Locust User, а как один фоновый greenlet
с настраиваемой частотой публикации (--writer-rate) — так K (читатели) и
скорость публикации управляются независимо друг от друга:

    locust -f loadtests/locustfiles/ws_fanout.py --host http://app:8000 \\
           --chat-kind supergroup --writer-rate 5 -u 500 -r 50 -t 5m

Прогоните дважды — с --chat-kind group (fanout_on_write, до 500 участников,
см. FAN_OUT_WRITE_THRESHOLD) и с --chat-kind supergroup (active_subscribers) —
как просит промпт, "обе fanout-стратегии" отдельными прогонами.

────────────────────────────────────────────────────────────────────────────
ВАЖНАЯ НАХОДКА, изменившая способ измерения (см. loadtests/README.md,
раздел "Находка: ts в ws.new_message не то, чем кажется"):

Промпт предполагал мерить латентность как (время получения на клиенте) минус
(ts из payload, который billed как "уже есть в build_ws_event"). Но
build_ws_event действительно кладёт ts = event["created_at"] (app/chats/dtos/
delivery.py), а вот WSConnection.try_send() (app/chats/dtos/websocket.py)
БЕЗУСЛОВНО перезаписывает event["ts"] = now_utc().isoformat() прямо перед
постановкой в очередь на отправку — то есть к моменту, когда фрейм уходит по
сети, поле ts уже НЕ содержит исходное время события, а содержит время
постановки в очередь НА КОНКРЕТНОМ gateway, уже после Kafka + delivery router
+ Redis. Считать по этому полю — значит мерить только "хвост" пути (postavka
в очередь -> сокет -> сеть -> клиент), а не весь fanout end-to-end.

Мы НЕ трогаем app-код (это отдельный промпт, не про измерение) — вместо этого
тест сам встраивает временную метку отправки в тело сообщения
(payload["content"] = JSON с полем lt_sent_at) и меряет реальный end-to-end
delivery latency как (время получения на читателе) минус (lt_sent_at,
записанный писателем непосредственно перед POST). Это ЕДИНСТВЕННЫЙ способ
измерить честный end-to-end fanout latency без правки приложения — и именно
он репортится под именами delivery_fanout_on_write/delivery_fanout_on_read,
как просит п.3(b) промпта.

Для сравнения (не для acceptance-порогов, а просто чтобы КОЛИЧЕСТВЕННО
показать масштаб бага) тест ДОПОЛНИТЕЛЬНО репортит то же самое, но по
буквально требуемой промптом формуле (receive_time - payload["ts"]), под
именами delivery_ts_field_on_write/on_read — сравнение двух чисел в отчёте
Locust наглядно показывает, сколько "хвоста" реально видно через сломанное
поле ts.

Предположение о синхронизации часов: писатель и читатели меряют lt_sent_at/
recv_time через time.time() СВОЕГО процесса. Для честного результата запускайте
писателя и читателей в одном Locust-процессе на одной машине (стандартный
`locust -f ...` без --master/--worker) — так и так рекомендуется для baseline.
Для распределённого прогона (--master/--worker на разных хостах) потребуется
NTP-синхронизация хостов, иначе рассинхрон часов подмешается в latency.
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import json
import random
import time
from datetime import datetime
from uuid import uuid4

import gevent
import requests
import websocket
from locust import User, events, task

from loadtests.common.acceptance import Threshold, add_threshold_arg, check_and_report
from loadtests.common.manifest import load_manifest
from loadtests.common.net import synthetic_ip_for_user
from loadtests.common.settings import (
    API_V1_STR,
    HTTP_BASE_URL,
    LOADTEST_MANIFEST_PATH,
    LOADTEST_SPOOF_SOURCE_IP,
)
from loadtests.common.tokens import mint_access_token
from loadtests.common.ws_client import WSClient, build_ws_url

KEEPALIVE_INTERVAL_S = 25  # < WS_HEARTBEAT_TIMEOUT (75s), см. app/chats/config.py

FANOUT_NAME_BY_KIND = {
    "group": "delivery_fanout_on_write",
    "supergroup": "delivery_fanout_on_read",
    "channel": "delivery_fanout_on_read",
}
TS_FIELD_NAME_BY_KIND = {
    "group": "delivery_ts_field_on_write",
    "supergroup": "delivery_ts_field_on_read",
    "channel": "delivery_ts_field_on_read",
}
WRITER_REQUEST_NAME = "[writer] POST /chats/{chat_id}/messages/"


@events.init_command_line_parser.add_listener
def _add_args(parser):
    parser.add_argument("--manifest", default=LOADTEST_MANIFEST_PATH, help="Путь к manifest.json от seed.py")
    parser.add_argument(
        "--chat-kind",
        default="supergroup",
        choices=["group", "supergroup", "channel"],
        help="Какую fanout-стратегию гонять: group=fanout_on_write, supergroup/channel=active_subscribers",
    )
    parser.add_argument("--writer-rate", type=float, default=2.0, help="Сообщений в секунду от единственного писателя")

    add_threshold_arg(parser, "--fanout-p95-threshold-ms", 2000.0, "Порог p95 end-to-end delivery latency")
    add_threshold_arg(parser, "--fanout-p99-threshold-ms", 5000.0, "Порог p99 end-to-end delivery latency")
    add_threshold_arg(parser, "--fanout-min-samples", 20.0, "Минимум измерений latency, чтобы порог был осмысленным")


@events.test_start.add_listener
def _setup(environment, **kwargs):
    opts = environment.parsed_options
    manifest = load_manifest(opts.manifest)
    rng = random.Random()
    chat = manifest.random_chat(opts.chat_kind, rng)

    environment.loadtest_manifest = manifest
    environment.loadtest_chat = chat
    environment.loadtest_stopping = gevent.event.Event()

    print(
        f"[ws_fanout] цель: chat_id={chat.id} kind={opts.chat_kind} "
        f"members={len(chat.member_ids)} writer_rate={opts.writer_rate}/s"
    )

    environment.loadtest_writer_greenlet = gevent.spawn(_writer_loop, environment, chat, opts)


@events.test_stopping.add_listener
def _stop_writer(environment, **kwargs):
    environment.loadtest_stopping.set()


@events.quitting.add_listener
def _check_acceptance(environment, **kwargs):
    opts = environment.parsed_options
    kind_name = FANOUT_NAME_BY_KIND[opts.chat_kind]
    thresholds = [
        Threshold(f"{kind_name} p95", kind_name, "WS", "p95_ms", opts.fanout_p95_threshold_ms),
        Threshold(f"{kind_name} p99", kind_name, "WS", "p99_ms", opts.fanout_p99_threshold_ms),
        Threshold(f"{kind_name} samples", kind_name, "WS", "min_requests", opts.fanout_min_samples),
    ]
    check_and_report(environment, thresholds)


def _writer_loop(environment, chat, opts) -> None:
    """Единственный писатель. НЕ Locust User — обычный gevent-greenlet с requests.Session,
    репортит свои REST-запросы в статистику Locust вручную (events.request.fire),
    как и требует п.3(b) промпта для WS-измерений."""
    manifest = environment.loadtest_manifest
    writer = manifest.user(chat.owner_id)
    token = mint_access_token(writer.id, writer.username)
    headers = {"Authorization": f"Bearer {token}"}
    if LOADTEST_SPOOF_SOURCE_IP:
        headers["X-Forwarded-For"] = synthetic_ip_for_user(writer.id)

    session = requests.Session()
    url = f"{HTTP_BASE_URL}{API_V1_STR}/chats/{chat.id}/messages/"
    period = 1.0 / max(opts.writer_rate, 0.001)

    while not environment.loadtest_stopping.is_set():
        started = time.monotonic()
        sent_at = time.time()
        body = {"content": json.dumps({"lt_sent_at": sent_at, "lt_msg_id": str(uuid4())})}
        req_headers = {**headers, "Idempotency-Key": str(uuid4())}

        try:
            resp = session.post(url, json=body, headers=req_headers, timeout=10)
            elapsed_ms = (time.monotonic() - started) * 1000
            if resp.status_code == 201:
                environment.events.request.fire(
                    request_type="POST", name=WRITER_REQUEST_NAME, response_time=elapsed_ms,
                    response_length=len(resp.content), exception=None, context={},
                )
            else:
                environment.events.request.fire(
                    request_type="POST", name=WRITER_REQUEST_NAME, response_time=elapsed_ms,
                    response_length=0, exception=RuntimeError(f"status={resp.status_code} body={resp.text[:200]!r}"),
                    context={},
                )
        except Exception as exc:  # noqa: BLE001 - репортим любую ошибку транспорта как failure
            elapsed_ms = (time.monotonic() - started) * 1000
            environment.events.request.fire(
                request_type="POST", name=WRITER_REQUEST_NAME, response_time=elapsed_ms,
                response_length=0, exception=exc, context={},
            )

        gevent.sleep(max(period - (time.monotonic() - started), 0))


def _parse_lt_sent_at(content: str | None) -> float | None:
    if not content:
        return None
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return None
    value = data.get("lt_sent_at")
    return float(value) if value is not None else None


def _parse_ts_field(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts).timestamp()
    except ValueError:
        return None


class ReaderUser(User):
    """K читателей, все подписаны на один и тот же chat_id (environment.loadtest_chat)."""

    host = HTTP_BASE_URL
    abstract = False

    def on_start(self) -> None:
        chat = self.environment.loadtest_chat
        manifest = self.environment.loadtest_manifest
        opts = self.environment.parsed_options

        rng = random.Random()
        self.user = manifest.user(rng.choice(chat.member_ids))
        self.chat_id = chat.id
        self.fanout_name = FANOUT_NAME_BY_KIND[opts.chat_kind]
        self.ts_field_name = TS_FIELD_NAME_BY_KIND[opts.chat_kind]

        token = mint_access_token(self.user.id, self.user.username)
        url = build_ws_url(token, initial_chat_id=self.chat_id, initial_last_seq=0)

        connect_started = time.monotonic()
        try:
            self.client = WSClient(url)
        except Exception as exc:
            self.environment.events.request.fire(
                request_type="WS", name="ws_connect", response_time=(time.monotonic() - connect_started) * 1000,
                response_length=0, exception=exc, context={},
            )
            raise

        self.environment.events.request.fire(
            request_type="WS", name="ws_connect", response_time=(time.monotonic() - connect_started) * 1000,
            response_length=0, exception=None, context={},
        )

        self._stopping = gevent.event.Event()
        self._recv_greenlet = gevent.spawn(self._recv_loop)
        self._keepalive_greenlet = gevent.spawn(self._keepalive_loop)

    def _keepalive_loop(self) -> None:
        while not self._stopping.is_set():
            gevent.sleep(KEEPALIVE_INTERVAL_S)
            try:
                self.client.send_json({"op": "ping"})
            except Exception:
                return

    def _recv_loop(self) -> None:
        while not self._stopping.is_set():
            try:
                frame = self.client.recv_json(timeout=5)
            except websocket.WebSocketTimeoutException:
                continue
            except Exception:
                if self._stopping.is_set():
                    return
                self._reconnect()
                continue

            self._handle_frame(frame)

    def _handle_frame(self, frame: dict) -> None:
        if frame.get("type") != "new_message":
            return
        recv_time = time.time()
        payload = frame.get("payload") or {}

        sent_at = _parse_lt_sent_at(payload.get("content"))
        if sent_at is not None:
            self.environment.events.request.fire(
                request_type="WS", name=self.fanout_name, response_time=(recv_time - sent_at) * 1000,
                response_length=len(json.dumps(frame)), exception=None, context={},
            )

        ts_value = _parse_ts_field(frame.get("ts"))
        if ts_value is not None:
            self.environment.events.request.fire(
                request_type="WS", name=self.ts_field_name, response_time=(recv_time - ts_value) * 1000,
                response_length=0, exception=None, context={},
            )

    def _reconnect(self) -> None:
        token = mint_access_token(self.user.id, self.user.username)
        url = build_ws_url(token, initial_chat_id=self.chat_id, initial_last_seq=0)
        for attempt in range(5):
            if self._stopping.is_set():
                return
            try:
                self.client.close()
                self.client = WSClient(url)
                return
            except Exception:
                gevent.sleep(min(2**attempt, 10))

    def on_stop(self) -> None:
        self._stopping.set()
        self.client.close()

    @task
    def idle(self) -> None:
        # Вся полезная работа читателя идёт в фоновых greenlet'ах (_recv_loop,
        # _keepalive_loop) — эта task существует только чтобы раннер Locust
        # держал пользователя живым и не считал его "без задач".
        gevent.sleep(1)
