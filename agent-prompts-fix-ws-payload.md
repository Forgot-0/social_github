# Промпты для агента: реализовать фикс в репозитории social_github

Корневая причина всех трёх проблем ОДНА: `ChatDeliveryRouter._enqueue_gateway_deliveries`
(`app/chats/services/delivery_router.py`) при сборке `MessagePayloadWS` использует только
`chat` и `message`, полностью отбрасывая `event.payload` — а именно в нём реально лежат
`reader_id`, `target_user_id`, `emoji/count/changed_by` (домен-события сериализуются через
`asdict(event)` в `app/core/message_brokers/converters.py`, так что поля туда доходят;
`ChatEventPayload` их тоже принимает благодаря `extra="allow"` — теряются они только на
этом последнем шаге сборки WS-пейлоада).

Промпты рассчитаны на агента с доступом к репозиторию (Claude Code и т.п.). Давайте их по
одному — каждый содержит проверенные ссылки на файлы/классы, чтобы агент не гадал структуру
проекта.

---

## Промпт 1 — базовый фикс: прокинуть extra-поля события в WS-payload

```
Репозиторий: social_github (FastAPI + Kafka + WS-gateway, чаты в app/chats).

Проблема: в app/chats/services/delivery_router.py, метод
ChatDeliveryRouter._enqueue_gateway_deliveries, WS-payload собирается так:

    payload=MessagePayloadWS(chat=chat, message=message).model_dump()

Это отбрасывает исходный event.payload (ChatEventPayload, объявлен в
app/chats/schemas/ws.py с model_config = ConfigDict(extra="allow")), в котором
реально приезжают доп. поля конкретных доменных событий:
- ReadedMessageEvent.reader_id (app/chats/models/message.py)
- KickedChatMemberEvent.target_user_id, requester_id
- BannedChatMemberEvent.target_user_id, requester_id, ban
- LeftChatMemberEvent.user_id
- ReactionUpdatedEvent.emoji, count, changed_by (app/chats/models/reaction.py)

Эти поля реально публикуются в Kafka (app/core/message_brokers/converters.py
использует asdict(event) — ничего не теряется на этом этапе), но не доходят до
клиента, потому что route_broker_message передаёт в WsEvent только chat_id/
message_id/sender_id, а _enqueue_gateway_deliveries вообще не смотрит в
event.payload при сборке MessagePayloadWS.

Задача:
1. Найди объявление ChatEventPayload (app/chats/schemas/ws.py) и подтверди,
   что extra="allow" действительно сохраняет незадекларированные поля в
   .model_extra — если сомневаешься, напиши короткий scratch-тест на
   pydantic-модели, чтобы убедиться перед тем как что-то менять.
2. Расширь MessagePayloadWS (app/chats/dtos/delivery.py) полем для
   произвольных доп. данных события, например:
       event: dict[str, Any] = Field(default_factory=dict)
   (не переиспользуй имена chat/message — их семантику менять нельзя, это
   ломает уже задокументированный контракт remaining событий типа
   new_message/message_edited, которым эти доп.поля не нужны).
3. В ChatDeliveryRouter.route_broker_message (или в WsEvent.build — выбери
   более подходящее по архитектуре место) прокинь event.payload.model_extra
   (или model_dump(exclude={"chat_id","message_id","sender_id"},
   exclude_none=True) — оцени сам, что чище) до места, где строится
   MessagePayloadWS в _enqueue_gateway_deliveries, и подставь в новое поле
   event.
4. Прокинь то же самое и в ветку _publish_offline_signal (там сейчас payload
   строится вручную как словарь на строках ~132-141 delivery_router.py —
   туда тоже нужно докинуть extra-поля события, иначе офлайн-доставка
   (fanout-on-write чаты) останется без фикса).
5. НЕ трогай существующие поля chat/message и их текущую семантику — цель
   чисто аддитивная: клиенты, которые уже делают no-op/рефетч на случай
   отсутствия этих полей, не должны сломаться (просто теперь у них появится
   возможность не рефетчить).
6. Обнови DeliveryDTO/MessagePayloadWS докстринги, если есть.
7. Прогони существующие тесты на чаты (tests/chats/integration/api/
   test_ws_integration.py, test_ws_access_and_resume.py) — они не должны
   сломаться.

Не переусложняй: если увидишь, что часть событий (messages_read) в текущей
реализации вообще не тянет message_id и поэтому message всегда None — это
отдельный нюанс, не блокирующий эту задачу, зафиксируй его отдельным TODO/
комментарием, не пытайся тут же чинить.
```

---

## Промпт 2 — `messages_read` → `reader_id` в WS-событии + тест

```
Контекст: после Промпта 1 механизм прокидывания extra-полей события в WS-
payload уже есть. Нужно закрыть конкретный кейс.

Задача:
1. Убедись, что для события "chats.message.readed" (публикуется в
   app/chats/commands/messages/mark_read.py, класс ReadedMessageEvent —
   поля chat_id, seq, reader_id) итоговый WS-фрейм с type="messages_read",
   доставленный клиенту, теперь содержит reader_id (и seq — он тоже полезен
   клиенту для точного обновления галочек "прочитано", сейчас он тоже
   потенциально теряется тем же путём).
2. Напиши интеграционный/unit-тест (ориентируйся на структуру
   tests/chats/integration/api/test_ws_integration.py и
   tests/chats/integration/ws_asgi_client.py — там уже есть хелпер для
   поднятия WS-соединения в тестах): пользователь A читает сообщения через
   MarkAsReadCommand → пользователь B, подписанный на чат по WS, получает
   messages_read с reader_id == A.user_id.
3. Обнови app/api-docs.md, раздел 7.4, строку с `messages_read` в таблице —
   убери формулировку "текущая реализация delivery-router всё равно требует
   message_id..." и опиши реальную новую форму payload с reader_id (и seq,
   если решишь его тоже прокинуть).
4. Не удаляй и не переписывай клиентскую логику — эта задача только про
   бэкенд и доки.
```

---

## Промпт 3 — `member_kick`/`member_banned`/`member_left` → `target_user_id`

```
Контекст: KickedChatMemberEvent и BannedChatMemberEvent
(app/chats/models/chat.py) уже содержат target_user_id и requester_id;
BannedChatMemberEvent — ещё и ban: bool (bool различает бан/разбан).
LeftChatMemberEvent содержит user_id (это и есть тот, кто вышел).

Задача:
1. После Промпта 1 проверь, что для всех трёх событий
   (chats.member.kicked / chats.member.banned / chats.member.left)
   соответствующие поля (target_user_id + requester_id для kick/banned;
   user_id для left; ban для banned) доходят до клиента в WS-фрейме.
2. Обрати внимание на member_banned: клиенту важно различать бан и разбан
   (BannedChatMemberEvent.ban). Убедись, что поле ban не потерялось при
   сериализации так же, как остальные — проверь явно отдельным тестом,
   т.к. это bool и его легче случайно не заметить в extra-словаре.
3. Напиши тесты по образцу tests/chats/integration/api/test_ws_integration.py:
   - kick другого участника → у него в WS payload.event.target_user_id ==
     ID кикнутого, у остальных участников чата — тоже (это broadcast-событие,
     не персональное);
   - ban с ban=True и последующий unban (ban=False, если это тоже шлёт
     BannedChatMemberEvent — проверь по коду, как разбан реализован) →
     оба состояния различимы в WS payload;
   - member_left → user_id совпадает с вышедшим.
4. Обнови таблицу в app/api-docs.md, раздел 7.4 (строки про member_left/
   member_kick/member_banned) — убери формулировку "при доставке через
   брокерный router" без деталей, распиши точную форму payload с новыми
   полями.
5. Не убирай REST-эндпоинт получения списка участников — рефетч чата
   клиентом при получении этих событий остаётся валидной стратегией даже
   после фикса (просто станет опциональной оптимизацией, а не единственным
   рабочим способом).
```

---

## Промпт 4 — `reaction_update` → `emoji/count/changed_by` + фикс нестыковки в доках (6.4 vs 6.7.5)

```
Контекст: ReactionUpdatedEvent (app/chats/models/reaction.py) содержит
message_id, chat_id, emoji, count, changed_by — но:
(a) эти поля не доходят до клиента (общая причина — Промпт 1);
(b) в api-docs.md есть реальная нестыковка: раздел 6.4 (строка 907) прямо
    говорит "В MessageDTO НЕТ поля reactions", а раздел 6.7.5 (строка 1078)
    содержит комментарий "message уже содержит актуальный reactions" в
    примере WS-payload. Я проверил код (app/chats/dtos/messages.py,
    MessageDTO) — поля reactions там действительно нет, 6.4 говорит правду,
    6.7.5 — нет.

Нужно решить это на уровне АРХИТЕКТУРЫ, а не просто поправить текст:

Вариант A (минимальный, рекомендуемый): НЕ добавлять reactions в MessageDTO.
Просто убедиться, что после Промпта 1 emoji/count/changed_by приходят в
WS-payload напрямую (payload.event.emoji/count/changed_by), и явно
задокументировать, что message.reactions по-прежнему не существует —
сводку реакций клиент получает либо из этих полей события (инкрементально),
либо через GET .../reactions/ (раздел 6.7.1) при первой загрузке чата/
пересоединении. Это соответствует уже существующей архитектуре (отдельная
таблица message_reaction_counters, отдельный эндпоинт).

Вариант B (более крупный): реально добавить summary-реакций в MessageDTO
(например reactions: list[ReactionSummaryDTO]), populate её в
MessageRepository при построении DTO, и тогда комментарий в 6.7.5 станет
правдой, а GET .../reactions/ останется нужен только для списка
проголосовавших (шторка "кто поставил", раздел 6.7.3).

Задача:
1. Реализуй Вариант A, если явно не решишь, что Вариант B оправдан
   объёмом использования (посмотри, есть ли где-то во фронтенд-требованиях/
   README указание, что реакции обязаны приходить вместе с сообщением при
   обычной пагинации GET /messages/ — если такого требования нет, Вариант A
   дешевле и не трогает REST-контракт).
2. После фикса payload для type="reaction_update" должен содержать
   emoji/count/changed_by рядом с chat/message (message остаётся как есть,
   без reactions).
3. Поправь app/api-docs.md:
   - раздел 6.7.5: убери или исправь комментарий "message уже содержит
     актуальный reactions" — если выбрал Вариант A, явно напиши, что
     реакции по-прежнему не приходят внутри message, а приходят как
     отдельные emoji/count/changed_by в payload события;
   - раздел 7.4, строка про reaction_update: обнови форму payload;
   - убедись, что 6.4 и 6.7.5 после правки не противоречат друг другу —
     это и есть критерий приёмки.
4. Тесты по образцу tests/chats/integration/commands/reactions (там уже
   есть интеграционные тесты на команды set/remove reaction) и
   tests/chats/integration/api/test_ws_integration.py — добавь проверку,
   что WS-событие reaction_update после PUT .../reactions/{emoji}/
   содержит корректные emoji/count/changed_by.
5. Учти семантику "одна реакция на пользователя" из 6.7.2: замена эмодзи
   шлёт ДВА события reaction_updated (декремент старого, инкремент нового) —
   убедись, что тест это учитывает и не ожидает одно событие там, где их два.
```

---

## Промпт 5 — пересмотр архитектуры: спроектировать production highload-мессенджер уровня Telegram

```
Контекст (проверь сам по коду, ниже — то, что я уже нашёл, чтобы ты не
тратил время на повторное открытие всех файлов, но не доверяй слепо —
перепроверь ключевые факты перед тем как их критиковать):

ТЕКУЩАЯ АРХИТЕКТУРА (как я её вижу сейчас):
- Запись сообщения: POST /chats/{chat_id}/messages/ (REST, НЕ через WS) →
  app/chats/commands/messages/send.py. Порядковый номер сообщения в чате
  выдаётся через app/chats/repositories/chat.py:allocate_message_seq —
  UPDATE chats SET seq_counter = seq_counter + 1 ... RETURNING seq_counter,
  т.е. монотонный счётчик через row-lock ОДНОЙ строки chats на весь чат.
- Доменные события (message.sent/readed, member.kicked/banned/left,
  reaction_updated) публикуются в Kafka через outbox+Debezium
  (docker-compose.yaml: kafka + debezium + debezium_connector).
- Консьюмер (app/chats/consumers/delivery.py) читает событие, решает
  fanout-стратегию (app/chats/models/chat.py: fanout_strategy) —
  FANOUT_ON_WRITE (личка/маленькие группы), ACTIVE_SUBSCRIBERS
  (супергруппы и группы больше chat_config.FAN_OUT_WRITE_THRESHOLD),
  CHANNEL_SUBSCRIBERS (каналы) — и раскладывает доставку по получателям
  через ChatDeliveryRouter (app/chats/services/delivery_router.py).
- Доставка до конкретного gateway-процесса идёт через Redis Stream на
  gateway (app/core/websocket/manager.py): consumer group + xreadgroup +
  xautoclaim для переподхвата зависших/упавших consumer'ов, maxlen-трим
  потока. Это даёт at-least-once ДОСТАВКУ УВЕДОМЛЕНИЯ до живого gateway,
  но не является источником истины — источник истины остаётся Postgres.
- WS-протокол (app/chats/routes/v1/ws.py, app/chats/schemas/ws.py):
  клиент → сервер только subscribe/unsubscribe/resume/ping/pong (никаких
  "отправить сообщение" через WS нет — это чисто read/control канал).
  Ресинхронизация после реконнекта — команда resume с cursor
  {chat_id: last_seq} (максимум 20 чатов за раз, ответ ws.history с
  батчем сообщений после seq и has_more) — app/chats/commands/websockets/
  resume.py.
- Presence — отдельный сервис на Redis (app/core/websocket/presence.py).
- Хранилище: только Postgres (docker-compose.yaml: postgres:18.3),
  вложения — MinIO (S3-совместимо). Нет CQRS/отдельного read-store для
  истории сообщений, нет упоминания шардирования Postgres или
  read-реплик в текущих compose-файлах.

Твоя задача — НЕ чинить конкретные баги (это уже сделано в промптах 1-4
выше), а критически пересмотреть архитектуру целиком и предложить СВОЮ
production-ready highload-архитектуру мессенджера уровня Telegram —
именно то, что уходит по WebSocket в обе стороны, и то, как отдаются
сообщения чата (запись + чтение истории + realtime-доставка).

Ход работы:

1. ЗАФИКСИРУЙ ЦЕЛЕВЫЕ ЦИФРЫ, от которых отталкиваешься (не пиши
   "highload" абстрактно): например N одновременных WS-соединений на
   инстанс, пиковые сообщений/сек на самый горячий чат/канал (важно для
   критики allocate_message_seq), максимальный размер группы/канала,
   требования к задержке доставки (p99), к какому SLA по потере
   сообщений при падении gateway/consumer стремимся. Явно напиши эти
   допущения в начале документа — вся дальнейшая критика и решения
   должны на них ссылаться, а не быть общими рассуждениями "как у
   Telegram/Discord".

2. КРИТИЧЕСКИ ОЦЕНИ КАЖДЫЙ из следующих пунктов ТЕКУЩЕЙ архитектуры —
   для каждого явно ответь: это реальная проблема при заданных цифрах
   из п.1, или это нормальное разумное решение, которое трогать не
   стоит (не надо ломать то, что уже хорошо спроектировано):
   a) allocate_message_seq как UPDATE одной строки chats — это
      сериализует все записи в один горячий чат/канал на уровне БД.
      Достаточно ли этого при пиковой нагрузке из п.1, или нужен другой
      механизм генерации порядка (например, per-partition монотонный
      счётчик в Redis с батч-выдачей диапазонов, Snowflake-подобные ID
      с последующей сортировкой на чтении, log-based подход как у
      Kafka-partition-per-chat)?
   b) Три fanout-стратегии (FANOUT_ON_WRITE/ACTIVE_SUBSCRIBERS/
      CHANNEL_SUBSCRIBERS) и порог FAN_OUT_WRITE_THRESHOLD — оцени,
      насколько это решение close к тому, что реально нужно на
      канале с миллионами подписчиков: как выглядит fanout для
      CHANNEL_SUBSCRIBERS сейчас (найди реализацию в
      ChatDeliveryRouter/consumers) и не станет ли она узким местом при
      огромном числе подписчиков.
   c) Redis Stream на gateway + xautoclaim — это конкретный, уже
      промышленный паттерн (аналог Kafka consumer group поверх Redis).
      Оцени границы применимости: maxlen-трим и что произойдёт, если
      gateway лежал дольше, чем maxlen/TTL стрима позволяют держать
      бэклог — подтверди (или опровергни), что resume-путь через
      Postgres полностью закрывает этот случай, или есть окно потери
      realtime-уведомления без последующего resume (например, если
      клиент не переподключается и не шлёт resume, а просто "висит").
   d) WS только для read/control, запись — через REST. Оцени этот
      выбор явно как архитектурное решение (а не как баг): плюсы
      (HTTP-инфраструктура: LB, ретраи, idempotency-key в заголовках,
      кэширование на CDN уровне для не-write методов) против минусов
      (лишний round-trip, две разные точки авторизации/rate-limit).
      Дай рекомендацию: оставить как есть (Discord-style: REST для
      записи + Gateway WS для событий) или перевести отправку сообщений
      в WS-op (Telegram MTProto-style: всё в одном канале) — и почему.
   e) Единственный Postgres как источник истины и read-store для истории
      сообщений (без шардирования/read-реплик/отдельного read-хранилища
      в текущих compose-файлах). Оцени, при каких объёмах истории на
      чат/пользователя это перестаёт масштабироваться на чтении
      (infinite scroll, поиск по истории) и что добавить: партиционирование
      таблицы messages по chat_id/времени, read-реплики, кэш последних
      N сообщений на чат в Redis, отдельный read-optimized store
      (Cassandra/ScyllaDB/ClickHouse) — обоснуй выбор под цифры из п.1,
      а не просто "потому что так у Discord".
   f) Multi-device: соединение хранит device_id (WSConnection), но
      посмотри, как (и посмотри — вообще ли) различаются per-device
      состояния прочитанности/подписок. Реальный Telegram-like мессенджер
      должен уметь: прочитано на одном устройстве → бейдж сброшен на
      всех остальных. Проверь, закрывает ли это текущий reader_id-фикс
      из Промпта 2 полностью, или для настоящей мультидевайс-синхронизации
      нужен отдельный per-device cursor (аналог Telegram getDifference
      / pts per device).
   g) Массовый холодный старт клиента (новое устройство логинится и должно
      получить состояние по ТЫСЯЧАМ чатов сразу) — текущий resume
      принимает cursor максимум на 20 чатов за раз (ResumeCommand). Оцени,
      достаточно ли этого для входа в аккаунт с 5000+ чатами, и как это
      делает Telegram (единый updates.getDifference с курсором на весь
      аккаунт, а не per-chat) — предложи, нужен ли отдельный REST/WS
      bulk-sync эндпоинт поверх текущего per-chat resume.

3. СПРОЕКТИРУЙ СВОЙ ВАРИАНТ. Обязательные разделы итогового документа:

   3.1. Схема данных, которые идут по WebSocket, В ОБЕ СТОРОНЫ:
        - Client → Server: полный список операций (envelope + payload для
          каждой), с явным решением по п.2.d (что остаётся в WS, что в
          REST), включая формат ack/идемпотентности при отправке
          сообщения (client-generated idempotency key/local_id для
          дедупликации при ретрае после разрыва соединения — в текущем
          коде это поищи в send.py, если есть — используй, если нет —
          обязательно добавь в свой протокол).
        - Server → Client: единый envelope (type/seq/chat_id/payload) —
          сравни с текущим WsEvent.build/MessagePayloadWS и предложи
          версионирование протокола (используй уже существующий механизм
          выбора subprotocol "chat.v1" в ws.py — предложи "chat.v2" для
          нового протокола, чтобы старые клиенты не ломались).
        - Явно распиши: нужен ли переход с JSON на бинарный протокол
          (protobuf/msgpack) и permessage-deflate сжатие при цифрах
          нагрузки из п.1, или JSON остаётся достаточным.

   3.2. Путь записи сообщения от клиента до всех получателей: где
        генерируется порядок (ответ на 2.a), где происходит fanout
        (ответ на 2.b), как гарантируется at-least-once/exactly-once
        на каждом хопе, что происходит при падении gateway/consumer/
        Kafka-партиции.

   3.3. Путь чтения истории чата: пагинация (курсор по seq, как сейчас,
        или что-то другое), холодный старт по всему аккаунту (ответ на
        2.g), кэширование горячих чатов, поиск по истории (если это
        требование — уточни, in-scope ли полнотекстовый поиск).

   3.4. Явный раздел "Что оставляем как есть и почему" — не переписывай
        то, что уже является адекватным production-паттерном (Redis
        Streams consumer group, outbox+Debezium, разделение fanout по
        типу чата) просто потому что "так принято у большого мессенджера".

4. ФОРМАТ РЕЗУЛЬТАТА: оформи как ADR-документ в docs/adr/ (создай папку,
   если её нет; посмотри, нет ли уже принятого формата ADR в репозитории —
   если есть шаблон, используй его). Плюс отдельный файл со схемами
   WS-протокола v2 (JSON Schema или pydantic-модели по образцу
   app/chats/schemas/ws.py — если предлагаешь заменить формат на protobuf/
   msgpack, дай .proto/схему отдельно).

5. Это ревью/дизайн-документ, а не немедленный рефактор всего кода:
   код не переписывай, если явно не попросят. В конце документа дай
   отдельный раздел "план миграции" (поэтапно, с учётом что
   chat.v1/chat.v2 может жить параллельно) — большой highload-сервис
   нельзя мигрировать одним PR.
```

---

## Как использовать

Промпты 2-4 логически зависят от Промпта 1 (общий механизм прокидывания
extra-полей) — давайте агенту их строго по порядку, после каждого просите
прогнать `pytest tests/chats` перед тем, как переходить к следующему.

Промпт 5 независим от 1-4 по коду (это ревью, а не патч) — но по смыслу
опирается на найденные в них баги (особенно на п. 2.f про мультидевайс и
reader_id), поэтому логичнее давать его последним, отдельной сессией, и
не просить агента параллельно ещё и патчить код по нему — это отдельная
дизайн-задача с отдельным результатом (документ, не diff).
