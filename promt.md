# Промпты для агента (HEAD текущего клона social_github)

Ниже — результат изучения кода перед постановкой задачи, в том же духе, что и `promt.md` в
репозитории: не гадаю, а указываю точные файлы/строки, где проблема подтверждена. Дальше — два
самостоятельных промпта, которые можно скормить агенту (Claude Code и т.п.) по одному за раз.

---

## Что подтверждено в коде перед промптом 1 (лимиты)

| Проблема | Где | Подтверждение |
|---|---|---|
| Rate-limit по IP, а не по user_id | `app/core/api/rate_limiter.py` (`ConfigurableRateLimiter` не переопределяет identifier), `app/main.py:44` (`FastAPILimiter.init(redis_client)` без `identifier=`) | `fastapi_limiter/identifier.py::default_identifier` берёт `request.client.host`. Значит `message_write_limiter` (`app/chats/routes/v1/messages.py`) и `reaction_write_limiter` (`app/chats/routes/v1/reactions.py`) лимитируют пул пользователей за одним NAT/прокси как одного клиента, а атакующий с ротацией IP лимит не почувствует вообще. |
| TOCTOU на `MAX_REACTIONS_PER_MESSAGE` | `app/chats/commands/reactions/set.py` (`SetReactionCommandHandler.handle`) | `count_distinct_emojis()` и `get_counter()` читаются **до** `reaction_repository.set_reaction()`. `SET_REACTION_SQL` в `app/chats/repositories/reaction.py` берёт `FOR UPDATE` только на строку `(message_id, user_id)`, а не на агрегат по сообщению — два параллельных запроса с разными новыми эмодзи на одном сообщении оба пройдут проверку `distinct_emojis >= MAX` и суммарно превысят лимит. |
| Voice/video-note лимиты по длительности и разрешению не применяются | `app/chats/config.py` (`MAX_VOICE_DURATION_SECONDS=600`, `MAX_VIDEO_NOTE_DURATION_SECONDS=60`, `MAX_VIDEO_NOTE_RESOLUTION_PX=640`), `app/chats/models/attachment.py:96,100` (`set_resolution`/`set_duration`) | `RequestAttachmentUploadCommandHandler` (`app/chats/commands/attachments/request_upload.py`) проверяет только `mime_type`/`file_size` до заливки. `ProccessAttachmentsCommandHandler` (`app/chats/commands/attachments/proccess.py`), который постобрабатывает файл после реальной заливки в MinIO, делает только magic-byte проверку MIME — ffprobe/аналог не вызывается, `set_duration`/`set_resolution` нигде не вызываются (0 call sites в `app/`). Часовой voice-message при этом пройдёт по размеру и никогда не будет пойман по длительности. |
| Нет rate-limit на WS-командах | `app/chats/commands/websockets/{ping,pong,subscribe,unsubscribe,resume}.py` | Ни одна из этих команд не имеет throttling-зависимости (в отличие от REST, где есть `Depends(message_write_limiter)`). `resume.py` при этом на каждый чат в курсоре делает `get_member_chat` + `get_chat_messages_after_seq` — до 20 чатов за один фрейм (`MaxLimitCursorError` ограничивает только количество, не частоту вызовов). Ничто не мешает клиенту слать `resume`/`subscribe` в цикле и класть Postgres. |

Промпт 1 ниже описывает именно это — больше ничего лишнего не добавлял.

---

## Промпт 1 — Лимиты и race conditions

```
Контекст: FastAPI модульный монолит, модуль app/chats — телеграм-подобный мессенджер.
Правила проекта из README ("Правила для AI-ассистентов") обязательны: не менять архитектуру,
паттерн Router → Command/Query → Handler → Repository → Model, DI только через Dishka providers.py,
RBAC/лимиты — не через if внутри бизнес-логики где для этого уже есть выделенный слой.
Каждое изменение сопровождается тестом в tests/chats (unit — без БД, integration — через
testcontainers, по аналогии с существующими).

Исправить четыре независимые проблемы. Каждую — отдельным коммитом с отдельными тестами.
Не трогай ничего, что не относится к перечисленному ниже (в частности — не трогай outbox,
profile projection, push-уведомления, поиск: это отдельные задачи).

1) Rate limiter должен идентифицировать по user_id, а не по IP.
   - Сейчас `ConfigurableRateLimiter` (app/core/api/rate_limiter.py) наследует поведение
     fastapi_limiter по умолчанию (identifier = request.client.host), это применяется в
     message_write_limiter и reaction_write_limiter.
   - Сделай identifier, который для авторизованных запросов берёт user_id из JWT (тот же
     механизм, что использует CurrentUserJWTData/JWTManager в этих же роутах), и только для
     неавторизованных (если такие есть на этих путях — проверь) откатывается на IP.
   - Не давай убрать сам rate limiting "потому что сложно" — если fastapi_limiter не поддерживает
     кастомный identifier per-instance удобно, покажи это явно и предложи решение (например,
     обёртку, которая формирует ключ до вызова fastapi_limiter, либо переход на identifier=
     параметр FastAPILimiter.init с извлечением user_id из request.state, если он туда кладётся
     мидлварой — проверь ContextMiddleware/LoggingMiddleware в app/core/middlewares, возможно
     user_id уже есть в request.state и его можно переиспользовать).
   - Тест: два запроса от разных user_id с одного IP не должны мешать друг другу; один user_id
     с разных IP должен упираться в лимит.

2) TOCTOU на MAX_REACTIONS_PER_MESSAGE в SetReactionCommandHandler.
   - Не переписывай архитектуру SET_REACTION_SQL (там уже корректный upsert с FOR UPDATE на
     (message_id, user_id) — это трогать не нужно).
   - Проблема именно в проверке лимита differents emoji до вставки. Сделай проверку атомарной
     относительно конкурентных вставок нового emoji на то же сообщение: варианты — advisory lock
     Postgres на message_id (pg_advisory_xact_lock) на время проверки+вставки, либо CHECK-триггер/
     constraint на стороне БД (например, ограничение через уникальный partial index + retry на
     23505 если insert новой строки в message_reaction_counters нарушит лимит), либо перепроверка
     count после insert с откатом (compensating: если после вставки строк с count>0 стало больше
     MAX — удалить только что вставленную и вернуть TooManyReactionsError). Выбери самый дешёвый
     по латентности вариант с учётом того, что на реакции ожидается высокий QPS — избегай глобальных
     локов, лочи именно на уровне конкретного message_id.
   - Тест: integration-тест с asyncio.gather на N параллельных SetReactionCommand с разными emoji
     на одно сообщение при MAX_REACTIONS_PER_MESSAGE=2 — после гонки distinct emoji не должно
     превышать 2.

3) Voice/video_note лимиты по длительности и разрешению — сделать реально работающими.
   - Добавь фактическую проверку в ProccessAttachmentsCommandHandler (app/chats/commands/
     attachments/proccess.py), в той же точке, где уже происходит magic-byte проверка MIME:
     после подтверждения реального MIME для voice/video_note скачай (или потоково прочитай)
     файл из StorageService и получи duration/resolution. Используй существующий сервис
     StorageService, не добавляй новую внешнюю зависимость без необходимости (в README есть
     прямой запрет добавлять сервисы "по умолчанию") — если для извлечения метаданных нужен
     ffprobe/ffmpeg, сначала проверь pyproject.toml/Dockerfile на предмет того, что уже
     установлено в образе, и используй его; если ничего нет — предложи минимальную зависимость
     (например, ffmpeg-python или прямой вызов ffprobe субпроцессом) и обоснуй выбор в PR-описании,
     не устанавливай её молча.
   - При превышении MAX_VOICE_DURATION_SECONDS / MAX_VIDEO_NOTE_DURATION_SECONDS /
     MAX_VIDEO_NOTE_RESOLUTION_PX — помечай attachment как AttachmentStatus.ERROR (тем же путём,
     что и MIME mismatch) вместо молчаливого пропуска.
   - Вызови существующие MessageAttachment.set_duration()/set_resolution() (app/chats/models/
     attachment.py) — они уже написаны, но никогда не вызываются, просто подключи их.
   - Тест: unit-тест на модель (set_duration/set_resolution уже могут иметь тесты — проверь
     tests/chats) + integration-тест ProccessAttachmentsCommandHandler с фикстурным
     voice/video файлом, превышающим лимит длительности/разрешения — статус должен стать ERROR.

4) Throttling на WS-командах.
   - Добавь per-connection/per-user ограничение частоты для ping/pong/subscribe/unsubscribe/resume
     (app/chats/commands/websockets/*.py). Не изобретай новый механизм — переиспользуй Redis (тот
     же, что уже инжектится в ChatConnectionManager/ChatDeliveryRouter) с простым fixed-window
     или token-bucket по ключу вида ws:ratelimit:{op}:{user_id}, через INCR+EXPIRE или Lua-скрипт,
     по аналогии с тем, как уже используются pipeline-операции в app/chats/services/ws.py.
   - При превышении — не рвать соединение молча: отправь `ws.error` с понятным кодом
     (например RATE_LIMITED) тем же способом, что уже используется в resume.py для NOT_CHAT_MEMBER,
     и после N нарушений подряд — закрывай соединение (переиспользуй manager.unregister с
     close_code, как это уже делается при WS_MAX_CONNECTIONS_PER_USER).
   - Добавь константы лимитов в ChatConfig (app/chats/config.py), не хардкодь числа в коде.
   - Тест: unit/integration тест, что после превышения частоты приходит ws.error с RATE_LIMITED,
     а не тихо игнорируется и не роняет обработчик.

Для каждого пункта — обнови api-docs.md, если там описано текущее поведение (rate limits уже
где-то документированы — не забудь). В конце — резюме в стиле promt.md: что было, что стало,
какие тесты добавлены, какие компромиссы принял и почему.
```

---

## Что подтверждено в коде перед промптом 2 (нагрузочные тесты)

- В репозитории нет ни locust, ни k6, ни каких-либо load-скриптов (`grep -r` по всему проекту —
  пусто). Нагрузочная готовность сейчас не подтверждена ничем, кроме unit/integration/e2e тестов
  (`tests/chats/{unit,integration,e2e}`, 42 файла — хорошее покрытие корректности, но не throughput).
- `docker-compose.yaml` уже поднимает всё нужное окружение: `app`, `consumers` (FastStream/Kafka
  воркер с `delivery.router`), `db`, `redis`, `kafka`, `debezium`, `debezium_connector`, `minio`,
  `queue_worker`, `scheduler`. Отдельного профиля/сервиса под нагрузочный инструмент нет.
- `monitoring/prometheus/prometheus.yml` уже скрейпит `kafka-exporter:9308` — lag consumer-группы
  `delivery-router` по топику `CHAT_TOPIC` технически доступен уже сейчас. Но специфичных для WS
  метрик нет нигде (`grep -rn "Gauge(\|Histogram(" app/chats/` не находит ничего, кроме модели
  `MessageReactionCounter`, которая метрикой не является): нет активных WS-соединений (gauge), нет
  latency от `SendedMessageEvent` до фактической доставки в сокет, нет длины/backlog per-gateway
  Redis Stream (`WebsocketKeys.gateway_stream_key`). Без этого результаты нагрузочного теста будет
  нечем объяснить при деградации.
- `tests/conftest.py` имеет `create_access_token`/`create_auth_headers` (pytest-фикстуры на базе
  `JWTManager`), но это pytest-only и не годится для standalone-скрипта нагрузки напрямую — токены
  для нагрузочного теста нужно минтить тем же секретом/алгоритмом отдельным скриптом.
- `app/init_data.py` сидирует только роли (auth/project/chat), никакого bulk-сидинга N
  пользователей / M чатов / участников для нагрузочного сценария нет — это тоже нужно сделать
  с нуля.
- WS-эндпоинт `app/chats/routes/v1/ws.py`: аутентификация через `?token=`/`?access_token=` в
  query, либо `Authorization: Bearer`, либо `Sec-WebSocket-Protocol: bearer.<token>`
  (`app/core/api/utils.py::get_ws_access_token`) — это определяет, как клиент нагрузочного теста
  должен подключаться.
- Fanout-стратегия зависит от `member_count`/типа чата (`Chat.fanout_strategy` в
  app/chats/models/chat.py, порог `FAN_OUT_WRITE_THRESHOLD=500`) — сценарии нагрузки обязаны
  отдельно гонять оба пути (`fanout_on_write` для мелких чатов и `active_subscribers` для
  супергрупп/каналов), это два разных кода с разной стоимостью.

## Промпт 2 — Нагрузочное тестирование

```
Контекст: тот же проект, модуль app/chats. Цель — не "написать нагрузочный тест ради теста",
а получить конкретные цифры (msg/sec, WS fanout latency p50/p95/p99, поведение под перегрузкой)
и зафиксировать их как baseline, чтобы дальнейшие изменения можно было сравнивать. Не запускай
против production/staging — только против локального docker-compose окружения.

0) Перед написанием сценариев — добавь минимально необходимую наблюдаемость, без которой
   результаты нагрузочного теста нельзя будет интерпретировать:
   - Gauge активных WS-соединений на gateway (по образцу того, как ChatConnectionManager уже
     ведёт connections_by_id/connections_by_user — просто экспортируй len() в prometheus_client
     Gauge, обновляемый в register()/unregister()).
   - Histogram задержки доставки: от момента публикации SendedMessageEvent (app/chats/models/
     message.py) в outbox до момента отправки в конкретный WS-фрейм в ChatConnectionManager.
     Не обязательно end-to-end через клиента — достаточно замерить на стороне сервера
     (timestamp события в payload уже есть — ts в build_ws_event, app/chats/dtos/delivery.py).
   - Gauge длины/backlog каждого gateway-стрима в Redis (XLEN на WebsocketKeys.gateway_stream_key)
     — можно снимать периодической задачей, аналогичной _refresh_routes_loop в
     app/chats/services/ws.py, не городи отдельный сервис.
   Подключи новые метрики туда же, где уже работает KafkaPrometheusMiddleware/registry (app/
   consumers.py) и метрики outbox (app/core/outbox/metrics.py) — используй тот же паттерн, не
   изобретай новый способ регистрации метрик.

1) Выбери инструмент и обоснуй: Locust (Python) предпочтителен здесь конкретно потому, что можно
   напрямую переиспользовать JWTManager/UserJWTData для минтинга токенов и модели/схемы из
   app/chats для валидации ответов, без дублирования контрактов на другом языке. Если выберешь
   k6 — обоснуй отдельно и опиши, как токены будут сгенерированы вне Python-процесса (например,
   отдельным Python-скриптом заранее, до прогона).
   Размести код в новой директории верхнего уровня loadtests/ (не в tests/ — это не pytest,
   не должно попадать в обычный test discovery и CI unit/integration прогон).

2) Сначала — скрипт сидинга данных (loadtests/seed.py или аналог): создать N пользователей
   напрямую в БД (без прохождения полного auth-флоу — это не предмет теста), M direct-чатов,
   K групповых чатов с размером ниже FAN_OUT_WRITE_THRESHOLD (500) и отдельно несколько
   супергрупп/каналов выше порога, чтобы протестировать обе fanout-стратегии
   (app/chats/models/chat.py::fanout_strategy). Параметры N/M/K должны быть аргументами
   командной строки, а не захардкожены.

3) Сценарии (минимум эти три, независимые друг от друга — отдельные Locust User classes/задачи
   k6, чтобы их можно было гонять по отдельности):
   a. REST throughput отправки сообщений: пул пользователей шлёт POST /messages/ в свои чаты
      с разумным Idempotency-Key (проверь, что ключ уникален на попытку, не на ретрай — иначе
      тест смеряет попадания в идемпотентный кэш, а не реальную запись), измерить msg/sec и
      p95/p99 латентность самого REST-ответа отдельно от latency доставки по WS.
   b. WS fanout latency: держим открытыми K WebSocket-соединений, подписанных на один и тот же
      чат (или на супергруппу — прогнать оба случая отдельно из-за разных fanout-стратегий),
      один "писатель" шлёт сообщения через REST, читатели фиксируют время от ts в полученном
      ws.new_message до факта получения на своей стороне — это и есть end-to-end delivery latency,
      сравнить с серверной histogram из пункта 0.
   c. WS connection churn + resume: массовое переподключение (закрыть/открыть соединения,
      вызвать resume с курсором) — проверить, что delivery router и Redis не деградируют при
      частом re-subscribe, и что после фикса rate-limit на WS-командах (промпт 1, пункт 4) тест
      это учитывает — не должен слать resume/subscribe быстрее лимита, иначе сценарий будет
      просто мерить RATE_LIMITED, а не реальную пропускную способность. Если промпт 1 ещё не
      выполнен на момент написания теста — сделай лимит частоты resume настраиваемым параметром
      сценария, чтобы можно было потом просто уменьшить интенсивность без переписывания скрипта.

4) Зафиксируй acceptance-критерии как код, а не только как текст в описании: сценарий должен
   явно падать (ненулевой exit code / Locust failure), если, например, p95 delivery latency
   в fanout_on_write превышает заданный порог, или error rate REST send превышает заданный
   порог. Значения порогов — параметры, не константы в коде теста, чтобы их было легко пересмотреть
   после первого прогона (baseline ещё не снят, поэтому на первый прогон это будут "мягкие"
   ориентировочные значения, которые нужно скорректировать по факту, а не угаданные заранее цифры).

5) Добавь docker-compose.loadtest.yaml (или профиль в существующем docker-compose.yaml) с
   отдельным сервисом под locust/k6, который может достучаться до app/consumers/redis/kafka по
   имени сервиса внутри app-network — не хардкодь localhost, окружение должно быть готово к
   `docker compose -f docker-compose.yaml -f docker-compose.loadtest.yaml up`.

6) По итогам первого прогона — не просто отчёт с цифрами, а конкретные находки: в какой момент
   растёт latency (число соединений? msg/sec? размер супергруппы?), что происходит с Kafka
   consumer lag delivery-router (уже виден в Grafana через kafka-exporter — используй существующий
   дашборд, не создавай новый с нуля, если существующий покрывает нужные панели) и с backlog
   gateway-стримов из пункта 0 в момент деградации. Зафиксируй baseline-числа в
   loadtests/README.md, чтобы дальнейшие PR могли на них ссылаться.

Не оптимизируй код по результатам этого промпта — только измерь и задокументируй. Оптимизации
(партиционирование messages, шардирование и т.п.) — предмет отдельного промпта после того, как
будут цифры, а не предположения.
```
