# Промпты для social_github: highload chats + offline-уведомления (Firebase) + тесты

Репозиторий: `Forgot-0/social_github` (модульный монолит на FastAPI). Эталон паттернов и
правила для агента — `README.md`, раздел «Правила для AI-ассистентов».

Порядок использования: **1 → 2 → 3**, затем **4** — независимый аудит всего приложения.
Промпт 3 предполагает, что дифф из 1 и 2 уже есть в рабочей копии.

## Сквозные правила для всех 4 промптов (не повторяются в каждом отдельно)

- **Изоляция модулей.** Проверено grep'ом по всему `app/`: сейчас НИ ОДИН из модулей
  (`app/auth`, `app/chats`, `app/profiles`, `app/projects`, `app/notifications`,
  `app/settings`) не импортирует код другого модуля напрямую — единственный общий код это
  `app/core`. Кросс-модульная связь идёт только через события в Kafka (консьюмер модуля B
  парсит `dict`, а не импортированный класс модуля A — см. `app/chats/consumers/
  profiles.py` и `app/profiles/consumers/user.py` как эталон). Это жёсткое правило,
  сохраняй его: **никаких `from app.<другой_модуль> import ...` или `import
  app.<другой_модуль>` нигде в новом коде.** Единственное разрешённое общее — `app.core`.
  Если задача требует данных из другого модуля — это сигнал, что данные должны прийти
  через Kafka-событие (payload как dict), а не через прямой вызов чужого репозитория/сервиса.
- **`loadtests/` — не трогать.** Директорию `loadtests/` (Locust-сценарии,
  `loadtests/README.md`) пишет и поддерживает другая команда/промпт. Не запускай, не
  редактируй и не полагайся на неё как на критерий приёмки в этих задачах.

---

## Промпт 1 — Highload-аудит и оптимизация `delivery_router.py` + `ws.py`

```
Контекст. Модульный монолит на FastAPI (см. README.md, раздел «Правила для
AI-ассистентов» — следуй строго). Модуль app/chats реализует Telegram-подобный чат:
REST + WebSocket-гейтвей, несколько подов гейтвея за балансировщиком, доставка через
Kafka + Redis Streams.

Поток данных сейчас: SendMessageCommandHandler (app/chats/commands/messages/send.py)
публикует доменное событие "chats.message.sent" в Kafka-топик chat_config.CHAT_TOPIC →
консьюмер app/chats/consumers/delivery.py вызывает ChatDeliveryRouter.route_broker_message
(app/chats/services/delivery_router.py) → для ChatFanoutStrategy.FANOUT_ON_WRITE обходит
ВСЕХ участников чата батчами (ChatRepository.iter_member_ids, до 500 участников — DIRECT/
GROUP), для ACTIVE_SUBSCRIBERS/CHANNEL_SUBSCRIBERS (SUPERGROUP до 1_000_000, CHANNEL до
10_000_000) — только активных подписчиков из Redis-множества ws:sub:chat:{chat_id} →
находит для онлайн-юзеров (gateway_id, connection_id) через ws:route:user:{user_id} →
кладёт события в Redis Stream конкретного гейтвея → ChatConnectionManager
(app/chats/services/ws.py) на каждом гейтвей-поде читает свой стрим consumer-группой и
рассылает по локальным WebSocket-соединениям.

ВАЖНО: строго соблюдай изоляцию модулей — app/chats не должен импортировать код других
модулей (app/auth, app/profiles, app/projects, app/notifications), только app/core.
Сейчас во всём проекте нет ни одного такого нарушения (проверено), не вноси ни одного.

Правь ИМЕННО app/chats/services/delivery_router.py и app/chats/services/ws.py. Пункты 5 и 6
ниже по необходимости требуют точечных правок в app/chats/dtos/websocket.py и
app/chats/queries/chats/get_members.py — это единственные разрешённые исключения,
объясни каждую такую правку в PR-описании. Код уже неплохой (батчинг через redis
pipeline, TTL на маршруты, эвикшн медленных consumer'ов, graceful shutdown) — не
переписывай архитектуру с нуля, ищи конкретные слабые места и точечно их закрывай.

Обязательные пункты (без права отложить без явного обоснования — по каждому нужен либо
код, либо, для пп. 2–3, зафиксированное решение с обоснованием в PR-описании):

1. Восстановление после падения consumer-а Redis Stream. stream_consumer =
   f"{gateway_id}:{os.getpid()}" — при рестарте пода PID меняется, имя консьюмера новое,
   pending-entries старого консьюмера в группе ws-gateway-{gateway_id} остаются
   непрочитанными навсегда. Добавь claim непрочитанных pending-entries при старте
   _consume_gateway_stream_loop (XAUTOCLAIM/XCLAIM), с учётом min-idle-time, чтобы не
   перехватывать записи, которые ещё реально обрабатывает живой процесс.

2. Параллелизм чтения стрима (РЕШЕНИЕ ОБЯЗАТЕЛЬНО, но не обязательно менять код). Сейчас
   один _consume_gateway_stream_loop на процесс, xreadgroup читает
   WS_GATEWAY_STREAM_READ_COUNT записей, дальше — asyncio.gather по батчу (уже конкурентно).
   Опиши, как бы ты замерил, реально ли не хватает параллелизма при целевой нагрузке, и
   либо обоснованно оставь как есть, либо реализуй решение. Не усложняй без цифр.

3. Блокировка _lock в ChatConnectionManager (РЕШЕНИЕ ОБЯЗАТЕЛЬНО). Единый asyncio.Lock на
   connections_by_id/connections_by_user/subscriptions_by_chat. Построчно подтверди — есть
   ли `await` внутри критических секций (сейчас похоже, что нет — критические секции чисто
   in-memory). Зафиксируй вывод и решение (шардировать лок сейчас или нет) в комментарии/
   PR-описании.

4. Observability. Добавь метрики Prometheus (prometheus_client уже используется в проекте,
   см. app/consumers.py — KafkaPrometheusMiddleware; если в проекте уже есть свой паттерн
   регистрации метрик, например app/core/outbox/metrics.py — используй его как образец, не
   изобретай новый способ). Минимум: активные соединения на гейтвей, активные подписки,
   счётчик эвикшенов по причине (connection limit / slow consumer / heartbeat timeout), lag
   стрима (XLEN / pending count), латентность доставки — используй ИСПРАВЛЕННОЕ поле `ts`
   и новое поле времени постановки в очередь из пункта 6 для честного расчёта
   end-to-end delivery latency, а не текущее (сломанное) поведение.

5. Судьба PresenceService — ОБЯЗАТЕЛЬНО ПРИНЯТЬ И ДОВЕСТИ ДО КОНЦА ОДНО ИЗ ДВУХ РЕШЕНИЙ,
   молчаливо отложить нельзя. Факт: PresenceService.set_online/set_offline
   (app/chats/services/presence.py) сейчас НИГДЕ не вызываются во всём app/ — это мёртвый
   код, is_online/get_online_status всегда будут давать неверный ответ в проде. Единственное
   текущее использование — app/chats/queries/chats/get_members.py (бейдж "онлайн" в списке
   участников чата).
   Вариант A — «Чиним». Подключи PresenceService.set_online в
   ChatConnectionManager.register (первое соединение пользователя) и в heartbeat/refresh-
   цикле, PresenceService.set_offline в unregister (когда у пользователя не осталось ни
   одного соединения ни на одном гейтвее — учти, что пользователь может быть подключён
   через несколько гейтвеев одновременно, offline нужно ставить только когда живых
   соединений не осталось вообще, а не при закрытии одного из нескольких). Добавь тесты
   на этот жизненный цикл.
   Вариант B — «Убираем». Если считаешь PresenceService избыточным (учитывая, что для
   реальной надёжности "онлайн ли юзер прямо сейчас" в проекте уже используется прямая
   проверка ws:route:user:{user_id}, а не отдельный presence-слой) — удали
   PresenceService целиком (файл, использование в providers.py, DI-провайдер) и перепиши
   get_members.py на прямую проверку через WebsocketKeys.user_route_key (то же самое, чем
   пользуется ChatDeliveryRouter._lookup_online_routes), не через отдельный ZSET presence.
   В любом случае: реши сам, какой вариант лучше с учётом качества UX (presence может
   давать более плавную семантику типа "был в сети N минут назад", а прямая проверка
   маршрутов — только бинарное "подключён прямо сейчас"), но ДОВЕДИ выбранный вариант до
   рабочего, протестированного состояния, никаких TODO/заглушек.

6. ОБЯЗАТЕЛЬНЫЙ фикс поля `ts` — правильное использование по всему пайплайну доставки,
   не просто патч одной строки. Баг: build_ws_event (app/chats/dtos/delivery.py) кладёт в
   ws_event["ts"] исходное время создания доменного события (event.created_at) — это
   бизнес-время "когда сообщение реально отправлено". delivery_router.py корректно
   прокидывает это значение дальше в _enqueue_gateway_deliveries. НО WSConnection.try_send()
   (app/chats/dtos/websocket.py) БЕЗУСЛОВНО перезаписывает event["ts"] = now_utc()... в
   момент постановки в очередь на конкретное соединение — из-за этого клиент теряет
   честное время события, и посчитать end-to-end delivery latency по полю ts невозможно
   (оно превращается в "время постановки в очередь", а не "время события", ещё и разное
   для каждого получателя одного и того же сообщения).
   Исправь: `ts` должен по всему пайплайну (build_ws_event → delivery_router → Redis Stream
   → ChatConnectionManager → try_send → клиент) оставаться исходным временем события и НЕ
   перезаписываться на каждом хопе. Добавь ОТДЕЛЬНОЕ поле (подбери имя сам, например
   enqueued_at или sent_at) для честного времени постановки в очередь конкретному
   соединению — именно оно используется для метрики delivery latency из пункта 4
   (latency = enqueued_at - ts). Проверь все места, где ts читается или тестируется
   (schemas/ws.py, существующие тесты вроде test_ws_integration.py, любая документация
   протокола) и приведи их в соответствие с новой, честной семантикой. Это меняющий
   контракт для клиентов WS-протокола (chat.v1) — если в проекте есть версионирование
   протокола, отметь это как совместимое расширение (новое поле добавляется, ts не
   переименовывается и не убирается, только перестаёт незаконно перезаписываться).

7. Публикация сигнала «получатели офлайн» для модуля notifications (нужно для отдельной
   задачи "офлайн push-уведомления через Firebase" — модуль notifications не может сам
   вычислить, кто офлайн, так как ему запрещено импортировать что-либо из app/chats
   — см. правило изоляции модулей выше). Реализуй ТОЛЬКО в _route_fanout_on_write
   (стратегия FANOUT_ON_WRITE — DIRECT/малые GROUP, до 500 участников). Для
   ACTIVE_SUBSCRIBERS/CHANNEL_SUBSCRIBERS НИЧЕГО не публикуй — полный обход миллионов
   участников ради этого сигнала недопустим, это должно остаться осознанным
   v1-ограничением, задокументируй его в коде и в PR-описании.
   Реализация: сразу после `routes = await self._lookup_online_routes(lookup_batch)`
   внутри _route_fanout_on_write у тебя уже есть routes: RouteMap (gateway_id → set
   online user_id) и lookup_batch (весь батч участников) — посчитай
   offline_user_ids = множество lookup_batch МИНУС объединение всех routes.values()
   (никаких дополнительных Redis-запросов не требуется, это переиспользование уже
   полученных данных). Если offline_user_ids не пуст — опубликуй сигнал через
   BaseMessageBroker.send_data(key=str(chat_id), topic=<НОВЫЙ_ТОПИК>, data={...})
   (BaseMessageBroker уже доступен через DI, см. app/core/message_brokers/base.py и
   app/core/di/broker.py). Данные обязаны быть самодостаточными (notifications не сможет
   ничего дозапросить у chats): chat_id, message_id, sender_id, offline_user_ids (список
   int), любые другие поля, которые реально нужны для текста/типа уведомления. НЕ отправляй
   текст сообщения (см. запрет на утечку контента в push-инфраструктуру третьей стороны —
   решается в промпте про notifications, но контракт формируешь ты).
   Заведи НОВУЮ константу топика в app/chats/config.py (например
   CHAT_OFFLINE_DELIVERY_TOPIC), НЕ переиспользуй CHAT_TOPIC — иначе собственный консьюмер
   ChatDeliveryRouter (app/chats/consumers/delivery.py, group=DELIVERY_ROUTER_GROUP_ID)
   тоже получит это сообщение и попытается ошибочно WS-маршрутизировать его. Публикация
   не должна быть частью транзакции/блокировать доставку онлайн-получателям — оберни в
   try/except, залогируй ошибку и не роняй остальную обработку батча при сбое паблиша
   (это best-effort сигнал, а не источник истины).
   ВАЖНО: имя топика, которое ты выберешь здесь, должно ТОЧНО совпасть с тем, что
   notifications-модуль будет использовать на своей стороне (independent redeclaration —
   см. правило изоляции модулей: значение дублируется как литерал в конфиге каждого
   модуля, общего импорта константы быть не может). Зафиксируй финальное имя и значение
   топика в PR-описании явно, чтобы автор задачи по notifications мог его использовать.

Смежные находки (НЕ чини, только зафиксируй в отчёте как кандидатов на отдельные промпты,
не входят в scope этой задачи):
- Rate limiting на WS control-plane командах (subscribe/resume) — сейчас отсутствует,
  физически лежит в app/chats/commands/websockets/subscribe.py и resume.py.
- ChatFanoutStrategy: GROUP физически не может достичь ACTIVE_SUBSCRIBERS
  (FAN_OUT_WRITE_THRESHOLD=500 == MAX_GROUP_MEMBERS=500 в app/chats/config.py и
  app/chats/models/chat.py).
- RATE_LIMITER_ENABLED (app/core/configs/app.py) — флаг объявлен, но нигде не читается.

Ограничения:
- Не меняй формат данных в Redis (ключи из app/chats/keys.py) без крайней необходимости —
  это ломает совместимость при rolling deploy старой/новой версии гейтвея одновременно.
  Если меняешь — опиши стратегию миграции/dual-read.
- Не добавляй новые внешние зависимости без необходимости — Redis Streams, Kafka,
  prometheus_client уже есть в проекте.
- Не трогай бизнес-логику отправки сообщений (send.py) и REST-контракты без явного запроса.
- Не импортируй ничего из app/auth, app/profiles, app/projects, app/notifications.
- Код обязан проходить `poetry run ruff check`, `mypy` и pylint на изменённые файлы.

Критерии приёмки:
- Все существующие тесты в tests/chats/** зелёные.
- Новые/обновлённые тесты покрывают пункты 1, 5, 6, 7 как минимум.
- `grep -rn "from app\.\(auth\|profiles\|projects\|notifications\)" app/chats/` — пусто.
- PR-описание с явным разбором каждого пункта 1–7: что сделано, какое решение принято по
  пп. 2, 3, 5 и почему, финальное имя топика из п.7.
```

---

## Промпт 2 — Офлайн push-уведомления через Firebase (модуль `app/notifications`)

```
Контекст. app/chats публикует (отдельной задачей, см. её результат перед началом работы —
файл app/chats/config.py, константа топика для офлайн-сигнала) на НОВЫЙ Kafka-топик
самодостаточное событие для чатов со стратегией FANOUT_ON_WRITE (DIRECT/малые GROUP):
chat_id, message_id, sender_id, offline_user_ids (список user_id без единого живого
WS-соединения на момент отправки сообщения). Для ACTIVE_SUBSCRIBERS/CHANNEL_SUBSCRIBERS
(супергруппы/каналы) сигнал не публикуется вообще — это осознанное v1-ограничение, не
пытайся его обойти самостоятельным опросом полного списка участников большого чата.

ЖЁСТКОЕ ПРАВИЛО ИЗОЛЯЦИИ МОДУЛЕЙ: весь код, который ты пишешь в app/notifications, НЕ
ИМЕЕТ ПРАВА импортировать что-либо из app.chats, app.auth, app.profiles, app.projects —
ни модели, ни сервисы, ни ключи Redis, ни конфиги. Разрешён только app.core. Всё, что тебе
нужно про офлайн-получателей, уже лежит в payload события с топика — не пытайся
самостоятельно проверять "онлайн ли пользователь" через Redis-ключи chats (WebsocketKeys)
или через PresenceService — они принадлежат app.chats и недоступны тебе по правилам.
Перед началом работы проверь: `grep -rn "from app\.\(chats\|auth\|profiles\|projects\)"
app/notifications/` должен быть пуст и оставаться пустым после твоих изменений.

Push-провайдер — Firebase Cloud Messaging. `firebase-admin` УЖЕ объявлен зависимостью в
pyproject.toml (>=7.5.0,<8.0.0), но нигде не используется и не сконфигурирован — не
добавляй новую библиотеку, используй эту.

Текущее состояние модуля (подтверди сам перед стартом):
- app/notifications/services/push/base.py — только абстрактный PushService
  (push(notification: Notification) -> None), ни одной реализации, ни одного
  DI-провайдера нигде в проекте.
- app/notifications/commands/notifications/push.py — PushNotificationCommand +
  PushNotificationCommandHandler существуют, но НЕ зарегистрированы в
  app/notifications/providers.py (NotificationModuleProvider) — ни в provide_all(...),
  ни в register_notification_commands.
- app/notifications/repositories/devices.py (DeviceRepository) умеет только create() —
  нет метода получить активные токены пользователя и нет метода деактивировать протухший
  токен. Тебе нужно оба добавить.
- app/notifications/models/device.py (UserDeviceToken) — есть token, platform
  (IOS/WEB/ANDROID), is_active — этого достаточно, менять модель не нужно.

Задача:

1. Новый Kafka-консьюмер app/notifications/consumers/chat_offline_delivery.py (имя на
   твоё усмотрение), подписан на топик из app/chats (значение бери из PR предыдущей
   задачи, задекларируй СВОЙ, независимый конфиг-константой в НОВОМ app/notifications/
   config.py — по образцу app/chats/config.py, значение строки топика должно ТОЧНО
   совпадать с chats-стороной, но объявляется отдельно, без импорта). Собственный
   group_id (новая константа, например OFFLINE_PUSH_GROUP_ID). Используй
   EventIdempotencyGuard (app/core/consumers/idempotency.py) со своей отдельной group.
   Добавь integration-тест (в промпте 3), который явно сверяет строковое значение топика
   на обеих сторонах (chat_config vs notification_config), чтобы поймать рассинхрон при
   рефакторинге любой из сторон.

2. Обработка события: распарси dict напрямую (НЕ создавай общий с chats класс события —
   каждый модуль валидирует свою сторону контракта независимо, см. правило изоляции).
   Для каждого user_id из offline_user_ids (кроме отсутствующих/некорректных — защитись
   от кривого payload) поставь в очередь задачу на пуш.

3. Тяжёлую работу (запись Notification в БД + вызов Firebase на каждого офлайн-
   пользователя) не делай синхронно в теле Kafka-хендлера — вынеси в Taskiq-задачу по
   образцу app/chats/tasks/success_attachment.py (BaseTask, __task_name__, @inject,
   FromDishka[BaseMediator]) — например app/notifications/tasks/
   push_offline_recipients.py. Консьюмер кладёт ОДНУ задачу на всё событие через
   QueueService.push с списком offline_user_ids; задача сама зовёт PushNotificationCommand
   на каждого (ограничь конкурентность — до 500 получателей на FANOUT_ON_WRITE-чат, но
   не отправляй 500 одновременных корутин без ограничения, используй семафор/чанки).

4. Зарегистрируй PushNotificationCommand + PushNotificationCommandHandler в
   NotificationModuleProvider (app/notifications/providers.py) — сейчас команда вообще не
   подключена к медиатору.

5. Заголовок/текст пуша — консервативно: НЕ читай Message.content (модели message нет и
   не может быть импортирована из chats), НЕ клади текст сообщения в payload пуша. title
   вида "Новое сообщение", payload = {"chat_id": ..., "message_id": ..., "sender_id": ...}.

6. Реализация PushService на Firebase — app/notifications/services/push/firebase/
   service.py (по структуре как app/core/services/mail: abstract в base.py, конкретная
   реализация в подпапке). Обязательные технические детали:
   - firebase_admin SDK синхронный (блокирующий HTTP), не вызывай его методы напрямую в
     async-коде — оборачивай в asyncio.to_thread.
   - Инициализируй firebase_admin.initialize_app(credentials.Certificate(path)) ОДИН раз
     за процесс — учти, что повторный вызов initialize_app с тем же именем приложения
     кидает исключение; используй проверку через firebase_admin.get_app() /
     firebase_admin._apps либо именованное приложение, оберни инициализацию в DI-провайдер
     APP-скоупа (по образцу app/core/di/mail.py::MailProvider), чтобы она гарантированно
     выполнялась один раз за процесс.
   - Внутри push(notification) получи активные токены пользователя через новый метод
     DeviceRepository (см. п.7), сгруппируй по platform при необходимости, отправляй
     ОДНИМ батч-вызовом на пользователя, а не по одному токену
     (firebase_admin.messaging.send_each / send_each_for_multicast, лимит Firebase — до
     500 сообщений за вызов). Если у пользователя нет активных токенов — просто выйди
     без ошибки (пользователь может ещё не установил приложение/не выдал разрешение).
   - Обработай ответ по каждому токену: если Firebase вернул ошибку
     "unregistered"/невалидный токен (messaging.UnregisteredError или соответствующий
     код в BatchResponse) — деактивируй этот токен через DeviceRepository (не удаляй
     строку, ставь is_active=False), чтобы не долбить в мёртвый токен на каждое
     сообщение. Не роняй всю обработку пользователя из-за одного плохого токена среди
     нескольких устройств.
   - Конфигурация: новый app/notifications/config.py (по образцу app/chats/config.py) с
     полем пути к service-account JSON (например FIREBASE_CREDENTIALS_PATH) — не хардкодь
     путь, бери из .env/окружения так же, как остальные секреты в проекте (см.
     app/core/configs/base.py::BaseConfig). Обнови .env.example, если он есть в репозитории.
   - DI-провайдер: заведи Provider (Scope.APP) для firebase-приложения и для PushService,
     физически размести в app/notifications/providers.py (PushService — интерфейс,
     принадлежащий notifications, а не core — в отличие от почты, которая используется
     несколькими модулями, push нужен только здесь, поэтому не выноси в app/core/di).

7. Добавь в DeviceRepository (app/notifications/repositories/devices.py):
   - метод получить активные токены пользователя (например get_active_by_user_id);
   - метод деактивировать токен(ы) (например deactivate_tokens(tokens: Sequence[str])) —
     одним UPDATE, не по одному.

8. Зарегистрируй новый роутер консьюмера в app/consumers.py (import + broker.include_router
   в setup_router — по аналогии с delivery.router/profiles.router/user.router).

Явно НЕ делай в рамках этой задачи:
- Не трогай app/settings/model/notification.py (UserNotificationSettings, mute/quiet-hours)
  — модель даже не зарегистрирована в app/core/models.py/Alembic сейчас, весь
  settings-модуль — только модели без repositories/commands/routes. Отдельная задача.
- Не пытайся заново реализовать в notifications то, что уже вычислено в chats
  (кто офлайн) — используй только payload события.
- Не создавай "Log/Null" заглушку PushService "на всякий случай" — целевая реализация
  одна, Firebase; фейковую реализацию для тестов заводи только в тестовом DI-провайдере
  (см. промпт 3), не в основном коде приложения.

Ограничения: следуй всем правилам из README.md («Правила для AI-ассистентов») — DI только
через Dishka, паттерн Command/Handler, никакой бизнес-логики внутри консьюмера напрямую.

Критерии приёмки:
- `poetry run ruff check app/notifications`, mypy, pylint — чисто.
- `grep -rn "from app\.\(chats\|auth\|profiles\|projects\)" app/notifications/` — пусто.
- Событие с offline_user_ids → для каждого создаётся Notification (is_read=False,
  type=CHAT) и вызывается Firebase push с активными токенами этого пользователя.
- Пользователь без активных токенов → Notification создаётся, push не падает и не шлёт
  ничего лишнего.
- Протухший токен в ответе Firebase → деактивируется в БД, повторно не используется.
- Ни разу за весь модуль не появляется импорт из app.chats/app.auth/app.profiles/
  app.projects.
```

---

## Промпт 3 — Тесты к промптам 1 и 2

```
Контекст. Ты добавляешь тесты к изменениям из двух задач:
(A) highload-оптимизация app/chats/services/delivery_router.py и app/chats/services/ws.py,
включая: XAUTOCLAIM-восстановление, решение по PresenceService (вариант A или B — открой
итоговый код и определи, какой был выбран, тестируй фактически реализованное), фикс поля
ts (плюс новое поле enqueued_at/sent_at), публикацию офлайн-сигнала на новый Kafka-топик.
(B) офлайн push-уведомления через Firebase в app/notifications: новый Kafka-консьюмер,
Taskiq-задача, FirebaseAdminPushService (или как её назвали), новые методы
DeviceRepository, регистрация PushNotificationCommand в DI.
Считай, что дифф A и B уже есть в рабочей копии — если каких-то файлов ещё нет, останови
работу над соответствующим блоком и сообщи об этом, не выдумывай API.

Следуй тестовым конвенциям проекта:
- Маркеры расставляются по пути файла автоматически (tests/conftest.py::
  pytest_collection_modifyitems: unit/integration/e2e по подпапке), но модульный маркер
  (chats/notifications) на классе/файле проставляй руками, как в
  tests/chats/unit/test_ws_connection.py (@pytest.mark.unit, @pytest.mark.chats).
- integration-тесты поднимают реальные Postgres/Redis через testcontainers
  (tests/conftest.py: postgres_container, redis_container, redis_client, di_container).
- unit-тесты — без БД/Redis, с AsyncMock/фейками (см. tests/chats/unit/
  test_ws_connection.py как образец стиля).
- Для DI-подмен на интеграционном уровне — паттерн tests/chats/providers.py
  (ChatsIntegrationProvider, подключается в tests/conftest.py::di_container через
  create_container(TestProvider(), ChatsIntegrationProvider())). Заведи аналогичный
  tests/notifications/providers.py (NotificationsIntegrationProvider) с фейковым
  PushService (со списком .pushed для ассертов, без реального обращения к Firebase — НЕ
  подключай реальный firebase_admin в тестах) и подключи его в tests/conftest.py рядом
  с ChatsIntegrationProvider(). Kafka-продюсер/консьюмер в интеграционных тестах, судя по
  существующим tests/chats/integration/*, тоже подменяется — используй тот же подход,
  что и в существующих тестах для консьюмеров delivery/profiles, не изобретай новый.
- В tests/conftest.py::pytest_configure зарегистрирован список маркеров — маркера
  "notifications" там ещё нет, добавь `config.addinivalue_line("markers", "notifications:
  Тесты модуля notifications")`.

Часть 1 — tests/chats (аудит delivery_router.py / ws.py):

1. tests/chats/unit/test_delivery_router.py (НОВЫЙ файл). Без Redis/БД, Redis — AsyncMock
   с ручной настройкой pipeline().execute() / smembers / sscan_iter, ChatRepository —
   AsyncMock, BaseMessageBroker — AsyncMock (для проверки публикации офлайн-сигнала).
   Покрой:
   - route_broker_message: message is None → no-op; is_chat_domain_event() == False →
     no-op; отсутствие chat_id → warning + no-op; исключение из route_chat_event
     перехватывается и логируется, не пробрасывается наружу.
   - route_chat_event: чат не найден → warning + return; FANOUT_ON_WRITE →
     _route_fanout_on_write; любая другая стратегия → _route_to_active_subscribers.
   - _lookup_online_routes: валидные маршруты группируются по gateway_id; "битые" записи
     не попадают в результат; пустой список user_id → {}.
   - _enqueue_gateway_deliveries: пустой routes_by_gateway → pipe.execute() не вызывается;
     корректное разбиение на чанки по WS_GATEWAY_STREAM_USERS_PER_ENTRY; исключение из
     pipe.execute() пробрасывается наружу, но перед этим залогировано.
   - НОВОЕ (офлайн-сигнал): в _route_fanout_on_write, если часть батча участников не
     попала в routes (офлайн) — broker.send_data вызывается ровно один раз на батч с
     топиком из конфига и корректным payload (chat_id/message_id/sender_id/
     offline_user_ids); если офлайн-участников в батче нет — send_data не вызывается;
     для ACTIVE_SUBSCRIBERS/CHANNEL_SUBSCRIBERS-чата (через _route_to_active_subscribers)
     send_data НИКОГДА не вызывается, даже если формально можно было бы вычислить
     "офлайн" по known-подписчикам — это намеренное ограничение, зафиксируй тестом.
   - Ошибка publish офлайн-сигнала (broker.send_data бросает исключение) не должна
     прерывать доставку остальным онлайн-получателям батча — залогирована и проглочена.

2. tests/chats/unit/test_connection_manager.py (НОВЫЙ или расширь существующий). Redis —
   testcontainer redis_client (предпочтительно, для честности pipeline-семантики) либо
   AsyncMock. Покрой:
   - register/unregister happy path, включая п.5 задачи A (PresenceService): если
     реализован вариант "чиним" — set_online вызывается на первом соединении
     пользователя, set_offline — когда не осталось ни одного соединения ни на одном
     гейтвее (не на закрытии одного из нескольких); если реализован вариант "убираем" —
     тест на то, что PresenceService больше нигде не используется, и на новую реализацию
     GetChatMembersQuery через прямую проверку маршрутов.
   - WS_MAX_CONNECTIONS_PER_USER (=2): третье соединение того же user_id эвиктит САМОЕ
     СТАРОЕ (по connected_at), close_code=1012.
   - subscribe_chat/unsubscribe_chat: in-memory + Redis-ключи корректны, TTL соблюдается.
   - send_to_users_local: require_subscription=True/False фильтрация.
   - _send_or_unregister: переполненная очередь → close_code=1013, соединение убирается,
     остальная рассылка батча не ломается.
   - НОВОЕ (ts): WSConnection.try_send сохраняет исходный ts из переданного event и
     дополнительно проставляет новое поле времени постановки в очередь (имя — по факту
     реализации), для событий без исходного ts (например ws.ping) — ts всё равно
     проставляется как раньше.
   - Если реализован XAUTOCLAIM (п.1 задачи A) — integration-тест: pending-entry от
     "мёртвого" имени консьюмера (та же группа, другое имя consumer, xreadgroup без xack),
     новый ChatConnectionManager с другим consumer name должен рано или поздно её
     заклеймить и обработать, не потеряв.

3. tests/chats/integration/api/test_ws_multi_gateway.py (НОВЫЙ, реальный
   redis_container). Два экземпляра ChatConnectionManager с разными gateway_id на одном
   redis_client (либо два test_app()/di_container с override gateway_id). Пользователь A
   подписан через "gateway-1", пользователь B — через "gateway-2", оба участники одного
   чата; ChatDeliveryRouter.route_chat_event кладёт событие в оба gateway-стрима; оба
   получателя получают событие после вычитывания своих стримов.

4. tests/chats/integration/test_offline_signal_topic_contract.py (НОВЫЙ) — простой тест,
   импортирующий chat_config и notification_config (последний — только если задача B уже
   выполнена; если нет, ограничься chats-стороной и явным TODO) и сверяющий, что константы
   имени топика для офлайн-сигнала СОВПАДАЮТ буквально. Это единственная страховка от
   рассинхрона, раз прямой импорт между модулями запрещён.

5. Если добавлялись Prometheus-метрики — smoke-тест, что нужные counter/gauge/histogram
   существуют и меняются при соответствующих операциях.

Часть 2 — tests/notifications (НОВЫЙ пакет, сейчас отсутствует целиком):

Структура по образцу tests/chats: tests/notifications/__init__.py,
tests/notifications/conftest.py, tests/notifications/providers.py
(NotificationsIntegrationProvider), tests/notifications/unit/, tests/notifications/
integration/{api,commands,consumers}/. Не забудь __init__.py в каждой новой директории.

1. tests/notifications/unit/test_push_command_handler.py: PushNotificationCommandHandler
   с фейковым PushService (сохраняющим вызовы) — команда создаёт Notification нужного
   типа/заголовка и вызывает push ровно один раз; session.commit() вызывается один раз.

2. tests/notifications/unit/test_device_repository.py: новые методы
   get_active_by_user_id/deactivate_tokens — на реальной БД (testcontainer) или на
   in-memory сессии, как принято для репозиториев в проекте (см. существующие
   integration-тесты репозиториев других модулей как образец).

3. tests/notifications/unit/test_firebase_push_service.py: firebase_admin ПОЛНОСТЬЮ
   замокан (monkeypatch на firebase_admin.messaging.send_each / аналог) — не обращайся к
   реальному Firebase ни при каких условиях. Проверь: батч-вызов одним запросом на
   пользователя с несколькими токенами (не по одному); пользователь без токенов — не
   падает, ничего не отправляет; ответ с "unregistered"-ошибкой по одному из токенов →
   deactivate_tokens вызывается для этого токена и только для него, остальные токены не
   трогаются, исключение наружу не пробрасывается.

4. tests/notifications/integration/consumers/test_chat_offline_delivery_consumer.py
   (реальные Postgres+Redis testcontainers, фейковый PushService через
   NotificationsIntegrationProvider): скорми консьюмеру dict в точности той формы,
   которую публикует chats (chat_id/message_id/sender_id/offline_user_ids) — НЕ импортируй
   формирующий код из app.chats, просто построй dict руками по задокументированному в
   промпте 1 контракту. Проверь: для каждого user_id из offline_user_ids появилась
   Notification и был вызван PushService.push; событие с пустым offline_user_ids не
   создаёт ничего; некорректный/отсутствующий user_id в списке не роняет обработку
   остальных.

5. Идемпотентность: то же событие (тот же ключ идемпотентности), прогнанное дважды, не
   создаёт вторую Notification на одного и того же пользователя.

6. tests/notifications/integration/api/test_notifications_endpoints.py — в проекте уже
   СУЩЕСТВУЮТ app/notifications/routes/v1/notifications.py и devices.py без единого
   теста, это не связано напрямую с задачей B, но раз ты создаёшь весь пакет
   tests/notifications с нуля — заодно закрой и это: список уведомлений, mark_read,
   mark_all_read, unread_count, создание device-токена — по образцу
   tests/profiles/integration/api/test_profiles_endpoints.py.

Общее: прогони `poetry run pytest tests/chats tests/notifications -q`, всё зелёное,
`pytest -m notifications -q` реально находит новые тесты,
`grep -rn "from app\.\(chats\|auth\|profiles\|projects\)" tests/notifications/` — пусто
(тестовый код notifications тоже не должен импортировать chats напрямую — только через
руками построенные dict-фикстуры, задокументированные в комментарии со ссылкой на
контракт из промпта 1).
```

---

## Промпт 4 — Аудит тестового покрытия: обязательный минимум тестов для всего приложения

```
Контекст. Проект — модульный монолит на FastAPI с пятью доменными модулями (auth,
profiles, chats, projects, notifications) плюс app/core. Тесты лежат в
tests/<module>/{unit,integration/{api,commands,...},e2e}, с testcontainers для
Postgres/Redis (tests/conftest.py), маркерами unit/integration/e2e/<module>.
Директорию loadtests/ (Locust) не трогай — не входит в эту задачу, ей занимается
отдельная команда/промпт.

На момент написания этого промпта поверхностный аудит (текстовый grep по классам
*CommandHandler/*QueryHandler на предмет упоминания где-либо в tests/) даёт список из
~56 хендлеров без единого текстового упоминания в tests/. ЭТО ГРУБАЯ ЭВРИСТИКА, не факт
отсутствия покрытия — часть может быть косвенно протестирована через HTTP/WS-роут без
упоминания имени класса. Не доверяй списку вслепую — где сомневаешься, открой тест и
проверь, вызывается ли нужный путь кода фактически.

Задача 1 — построить объективную картину покрытия:
1. Прогони `poetry run pytest --cov=app --cov-report=term-missing --cov-report=html`,
   сохрани отчёт как артефакт задачи/CI-джобы (не коммить в git).
2. Построй таблицу: модуль → % покрытия строк → топ-10 самых крупных непокрытых файлов по
   числу строк. Приложи к результату задачи.

Задача 2 — устранить ПОДТВЕРЖДЁННЫЕ (не эвристические) пробелы, по приоритету:

1. app/notifications — если задачи "Firebase-уведомления" (см. отдельный промпт) ещё не
   выполнялись — модуль целиком без единого теста, tests/notifications/ не существует.
   Если та задача уже сделана вместе со своим промптом 3 по тестам — этот пункт закрыт,
   проверь фактическое покрытие через отчёт Задачи 1, а не по факту существования папки.

2. app/chats/services/delivery_router.py (ChatDeliveryRouter) — если задача highload-
   аудита ещё не выполнялась (см. отдельный промпт) — ни одного unit/integration-теста
   нигде. Если выполнена вместе со своим промптом 3 — проверь фактическое покрытие через
   отчёт, не полагайся на факт наличия файла.

3. app/chats/services/ws.py (ChatConnectionManager) — то же самое: если промпт про
   highload-аудит и промпт про тесты к нему уже выполнены, проверь по отчёту coverage,
   что реально покрыто (эвикшн, slow consumer, межгейтвейная маршрутизация, shutdown,
   recovery consumer-группы), а не только то, что файл теста появился.

4. app/chats/services/presence.py (PresenceService) — судьба должна быть уже решена
   промптом про highload-аудит (вариант "чиним" или "убираем", см. его п.5). Если решение
   ещё не принято — прими его сейчас как часть этой задачи (не оставляй мёртвый код без
   решения) и добавь тесты под фактически выбранный вариант.

5. app/chats/commands/reactions/{set,remove}.py — каталог
   tests/chats/integration/commands/reactions/ существует, но пуст (только __init__.py),
   REST-слой реакций (app/chats/routes/v1/reactions.py) тоже нигде не протестирован.
   Добавь integration-тесты по образцу tests/chats/integration/commands/messages/*.

6. app/chats/commands/profiles/backfill.py и app/chats/tasks/backfill_profiles.py — не
   встречаются в tests/.

Задача 3 — для ОСТАЛЬНЫХ хендлеров из эвристического списка (auth: oauth-флоу,
deactivate_session, roles add/delete-permissions/update, permissions get_list, users
get_list, sessions get_list*; chats: websocket-команды ping/pong/resume/subscribe/
unsubscribe, calls join/mute, attachments proccess/success/request_upload, queries
get_list/get_members/get_detail/get_context для чатов и сообщений; profiles:
proccess_avatar/update_avatar, queries; projects: delete/change_role/
update_permissions/update-role/create-role, queries get_my/get_my_invites/get_list):
- Проверь по отчёту coverage и по чтению существующих integration/api-тестов, реально ли
  строки хендлера выполняются существующими тестами косвенно.
- Если да — покрытие есть, отметь как "covered indirectly" в итоговом отчёте, ничего не
  делай.
- Если нет (строки в отчёте красные) — добавь тест уровня, адекватного риску: для чисто
  читающих query-хендлеров без сложной логики — один happy-path REST-тест; для команд с
  бизнес-правилами (RBAC-проверки, переходы состояний, лимиты) — покрой edge-cases по
  образцу tests/chats/integration/commands/chats/test_ban.py или
  test_change_role_extended.py как эталона глубины теста для таких кейсов в проекте.

Задача 4 — страж изоляции модулей. Добавь автоматизированную проверку (не полагайся
только на разовый grep): например tests/architecture/test_module_isolation.py — unit-тест
без внешних зависимостей, который парсит AST/импорты всех файлов под каждым
app/<module>/ и падает, если найден импорт из другого доменного модуля (кроме app.core).
На момент написания нарушений нет — тест должен пройти сразу и защищать от регресса.

Общие правила для всех новых тестов в этой задаче:
- Строго следуй существующим конвенциям: маркеры по модулю, testcontainers для
  integration, паттерн factories.py для тестовых данных, auth через
  create_access_token/create_auth_headers из tests/conftest.py.
- Не дублируй один и тот же сценарий на разных уровнях без причины.
- Не трогай loadtests/.

Критерии приёмки:
- Итоговый отчёт: таблица покрытия по модулям до/после, список "false positive" из
  эвристического списка (уже покрыто косвенно), список реально добавленного, список
  найденных по пути багов, вынесенных в отдельные тикеты, а не исправленных тут же (кроме
  PresenceService — его решить обязательно, см. Задачу 2, п.4).
- `poetry run pytest -q` — всё зелёное, включая маркер notifications и тест изоляции
  модулей из Задачи 4.
- `poetry run ruff check tests/` и mypy на новые тестовые файлы — чисто.
```
