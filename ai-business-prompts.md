# Промты для AI-агента по доработке `social_github`

Этот файл содержит не абстрактные требования «с нуля», а промты на основе того, что уже есть в проекте. Перед реализацией агент должен свериться с текущим кодом и не дублировать уже сделанные части.

## Что уже реализовано и от чего отталкиваться

- Outbox уже есть: модель `OutboxMessage` в `app/core/outbox/model.py`, репозиторий `app/core/outbox/repository.py`, запись событий через `MediatorEventBus` в `app/core/events/mediator/service.py`, Alembic-таблица `outbox_messages`, Debezium-конфиг `infra/debezium/outbox-connector.json`, автосоздание connector-а в `docker-compose.yaml`.
- Локальная проекция профиля для чатов уже начата: `ChatUserProfile` в `app/chats/models/profile.py`, DTO `ChatProfileDTO` в `app/chats/dtos/profiels.py`, репозиторий `app/chats/repositories/user_profile.py`, команда `app/chats/commands/profiles/upsert.py`, consumer `app/chats/consumers/profiles.py`.
- `MessageDTO` уже содержит `author_profile`, а модель `Message` уже имеет relationship на `ChatUserProfile`.
- Типы вложений `voice` и `video_note` уже добавлены в `AttachmentType`; MIME allowlist для voice/video-note уже есть в `app/chats/config.py`; upload request умеет принимать явный `attachment_type` для этих типов.
- Реакции на сообщения в чате полноценно ещё не реализованы. В проекте есть только настройки уведомлений про реакции в `app/settings`, но нет моделей/API/DTO/WebSocket-событий реакций чата.

## Общие правила для всех промтов

1. Сначала проверь текущую реализацию через `rg`/чтение файлов, а не добавляй новую сущность поверх существующей.
2. Сохраняй архитектуру проекта: Router → Command/Query → Handler → Repository → Model, Dishka DI, Alembic, доменные события и outbox.
3. Если меняется REST/WS контракт, обязательно синхронизируй `api-docs.md`.
4. Добавляй тесты именно на пробелы/баги в текущей реализации, а не на уже покрытые happy-path-и.
5. Не переименовывай публичные API без необходимости. Если внутреннее имя содержит опечатку, исправляй его только вместе с миграцией/совместимостью и обновлением импортов.

---

## Промт 1. Довести существующий Outbox + Debezium до production-ready состояния

```text
Ты работаешь в `social_github`. Outbox Pattern уже частично реализован, поэтому НЕ создавай новый outbox с нуля.

Текущая база:
- `app/core/outbox/model.py`: `OutboxMessage`, таблица `outbox_messages`, статусы `pending/published/failed`, attempts, available_at, published_at.
- `app/core/outbox/repository.py`: batch fetch, counters, cleanup, requeue.
- `app/core/events/mediator/service.py`: доменные события записываются в outbox через `OutboxMessage.create()`.
- `infra/debezium/outbox-connector.json`: Debezium Outbox Event Router уже настроен на `public.outbox_messages`.
- `docker-compose.yaml`: есть сервис/шаг регистрации connector-а.

Задача: провести аудит и закрыть недостающие места, чтобы outbox действительно был надёжным production-механизмом.

Что проверить и доработать:
1. Транзакционность:
   - убедись, что `MediatorEventBus.publish()` вызывается внутри той же SQLAlchemy-сессии и до commit бизнес-команды;
   - добавь тест, где бизнес-сущность и `outbox_messages` появляются одним commit-ом и оба откатываются при exception.
2. Debezium/WAL:
   - проверь, что PostgreSQL в compose действительно стартует с `wal_level=logical` и publication `social_outbox` создаётся для `outbox_messages`;
   - если publication/slot создаются неявно или нестабильно, добавь init script/документацию;
   - проверь соответствие enum-регистра: в модели enum значения `pending/published/failed`, а индексы/миграция используют `PENDING/FAILED`. Исправь только если это реально ломает Postgres partial indexes.
3. Семантика статусов:
   - при Debezium EventRouter запись не обязательно надо помечать `published`, потому что публикация происходит из WAL. Опиши выбранную стратегию: либо `published_at/status` используются только fallback publisher-ом, либо добавь отдельную cleanup-стратегию для Debezium-only режима;
   - не делай ложное `mark_published()` без подтверждения публикации.
4. Идемпотентность consumers:
   - проверь consumers `app/profiles/consumers/*`, `app/chats/consumers/*`, delivery router;
   - добавь обработку `eventId` из headers Debezium и таблицу/Redis-key processed events там, где повторная доставка может создать дубли;
   - если event-id сейчас недоступен в consumer payload, исправь converter/header mapping.
5. Observability:
   - добавь/проверь метрики pending/failed/oldest age;
   - добавь structured logs с `event_id`, `event_name`, `aggregate_id`, `topic`.
6. Документация:
   - обнови `api-docs.md` разделом для backend/AI-агентов: delivery semantics = at-least-once, порядок событий по aggregate_id, idempotency contract, Debezium local runbook.

Acceptance criteria:
- Нет второй outbox-таблицы и нет параллельной публикации напрямую в Kafka из бизнес-команд.
- Тест доказывает atomic write бизнес-данных + outbox.
- Debezium config и compose согласованы с реальной таблицей `outbox_messages`.
- Consumers безопасны к повторной доставке.
- В `api-docs.md` задокументирована текущая схема outbox, а не новая выдуманная схема.
```

---

## Промт 2. Исправить и завершить существующую локальную проекцию профиля в чатах

```text
В модуле чатов уже есть локальная проекция профиля. Нужно не создавать новую таблицу, а привести текущую реализацию к рабочему и документированному состоянию.

Текущая база:
- `app/chats/models/profile.py`: модель `ChatUserProfile`, таблица `chat_user_profiles`.
- `app/chats/dtos/profiels.py`: DTO `ChatProfileDTO` (обрати внимание на опечатку `profiels.py`).
- `app/chats/repositories/user_profile.py`: `get_by_ids`, `get_by_id`, `upsert`.
- `app/chats/commands/profiles/upsert.py`: команда обновления проекции.
- `app/chats/consumers/profiles.py`: consumer топика `profiles`.

Что нужно сделать:
1. Исправить несогласованность полей:
   - модель объявляет `avatar_s3_keys`, миграция тоже создаёт `avatar_s3_keys`, но DTO/repository используют `avatars`;
   - выбери единое имя, предпочтительно `avatars`, потому что `api-docs.md` и `ProfileDTO` описывают карту аватаров;
   - добавь Alembic-миграцию rename `avatar_s3_keys` → `avatars` или адаптируй mapper/property без ломания БД.
2. Исправить factory/typing баги:
   - `ChatUserProfile.create()` сейчас принимает `avatar_s3_key`, а присваивает `avatar_s3_key`, которого нет в модели;
   - поправь на выбранное поле и добавь unit-тест.
3. Идемпотентность и ordering:
   - сейчас `upsert()` сравнивает `ChatUserProfile.updated_at < revision`, но `revision` в команду не прокидывается из consumer-а;
   - добавь в команду `revision/event_updated_at` и `event_id`;
   - не применяй повторное событие и не перетирай новую проекцию старым event-ом;
   - если нет таблицы processed events, используй отдельную таблицу или расширь `chat_user_profiles` полями `last_event_id`, `source_updated_at`.
4. Consumer contract:
   - проверь реальные события, которые публикует profiles/auth модуль (`ProfileCreated`, `ProfileUpdated`, avatar processing);
   - consumer не должен падать от отсутствующего `username`, если событие профиля его не содержит; добавь fallback/merge с auth event или nullable `username`.
5. Backfill/reconciliation:
   - добавь management/taskiq-команду или отдельный скрипт для первичного заполнения `chat_user_profiles` из текущих профилей;
   - добавь короткую инструкцию запуска;
   - добавь метрику/лог количества обновлённых/пропущенных записей.
6. Тесты:
   - upsert создаёт проекцию;
   - повтор event-id не меняет запись;
   - старый revision не перетирает новый;
   - отсутствие optional fields не ломает consumer;
   - schema/model field names совпадают.
7. Документация:
   - обнови `api-docs.md`: указать, что профиль автора в чатах — eventual consistent локальная read-model и может временно быть `null`/устаревшим.

Acceptance criteria:
- В `ChatUserProfile`, repository, DTO и миграциях нет расхождения `avatar_s3_keys` vs `avatars`.
- Consumer чатов не падает на реальном payload профиля.
- Проекция не откатывается старым событием.
- Есть backfill/reconciliation путь.
```

---

## Промт 3. Реально подключить `author_profile`/`profile` к REST и WebSocket без N+1

```text
`MessageDTO.author_profile` и relationship `Message.profile` уже есть, но этого недостаточно: нужно проверить, что данные реально подгружаются и сериализуются во всех нужных REST/WS ответах.

Текущая база:
- `app/chats/dtos/messages.py`: `MessageDTO.author_profile` уже объявлен.
- `app/chats/models/message.py`: relationship `profile` на `ChatUserProfile` уже объявлен.
- `app/chats/repositories/message.py`: сейчас selectinload подгружает `reply_to`, `attachments`, `forwarded_from`, но не видно явной загрузки `profile` для самого сообщения и вложенных сообщений.
- `MemberChatDTO` в `app/chats/dtos/members.py` нужно проверить: если `profile` ещё нет, добавить.

Что нужно сделать:
1. Проверить сериализацию:
   - Pydantic ждёт поле `author_profile`, а ORM relationship называется `profile`; добавь mapper/property или ручное преобразование, чтобы `author_profile` реально заполнялся;
   - то же для `reply_to.author_profile` и `forwarded_from.author_profile`.
2. Избежать N+1:
   - в `MessageRepository.get_paginated_chat_messages`, `get_chat_messages_after_seq`, `get_message_context`, `get_by_id` добавить `selectinload(Message.profile)`;
   - для nested `reply_to/forwarded_from` также загрузить их profile, если SQLAlchemy-конфигурация позволяет;
   - если relationship неудобен, сделай batch-load через `ChatUserProfileRepository.get_by_ids()` и mapper service.
3. Участники:
   - расширь `MemberChatDTO` полем `profile: ChatProfileDTO | null`;
   - в `GET /chats/{chat_id}/members/` подгружай profiles батчем по `user_id`;
   - не убирай `user_id`.
4. Direct chat list/detail:
   - оцени, нужен ли `peer_profile` для direct-чата в `ChatDTO`/`ChatDetaiDTO`;
   - если добавляешь — только из локальной проекции и батчем, без синхронного обращения в profiles module.
5. WebSocket:
   - `ws.history.messages[]` должен использовать тот же `MessageDTO` с `author_profile`;
   - lightweight `new_message` можно оставить без профиля, но в `api-docs.md` явно напиши, что профиль приходит после REST fetch или в `ws.history`;
   - если добавляешь профиль в `member_joined`, брать его только из `chat_user_profiles` и делать nullable.
6. Тесты:
   - REST список сообщений возвращает `author_profile`, когда проекция есть;
   - REST detail сообщения возвращает `author_profile`;
   - `author_profile=null`, когда проекции нет;
   - nested reply/forward тоже содержит profile или документированно `null`;
   - список участников содержит `profile`;
   - WS history содержит обновлённый DTO.
7. Документация:
   - синхронизируй `api-docs.md` разделы 6.2, 6.3, 6.4, 7.4, 7.5 и Flutter checklist.

Acceptance criteria:
- Клиент действительно получает имя/аватар автора сообщения из REST без отдельного запроса в `/profiles`.
- Горячие запросы сообщений/участников не создают N+1.
- Старые поля `author_id` и `user_id` сохранены.
```

---

## Промт 4. Завершить voice messages и video notes, которые уже частично добавлены

```text
Voice/video-note поддержка уже частично есть в attachment layer. Не добавляй её повторно — доведи до полного end-to-end флоу.

Текущая база:
- `AttachmentType` уже содержит `VOICE = "voice"` и `VIDEO_NOTE = "video_note"`.
- `ChatConfig` уже содержит `ALLOWED_VOICE_MIMES` и `ALLOWED_VIDEO_NOTE_MIMES`.
- `RequestAttachmentUploadCommandHandler` уже умеет использовать `UploadRequest.attachment_type` для voice/video_note.
- `AttachmentDTO` уже имеет `duration_seconds`, `width`, `height`.
- `MessageType` пока, похоже, не содержит `voice`/`video_note`, поэтому отправка сообщения с этими типами может быть неполной.

Что нужно сделать:
1. MessageType/endpoints:
   - добавить `voice` и `video_note` в `MessageType`, request schemas и validation;
   - разрешить `content=null` для voice/video_note;
   - требовать ровно один attachment подходящего типа для voice/video_note сообщения;
   - не позволять отправить `message_type=voice` с image/file attachment и наоборот.
2. Upload limits:
   - сейчас voice/video_note MIME проверяются, но size/duration limits для них нужно проверить отдельно;
   - добавь `MAX_VOICE_SIZE`, `MAX_VOICE_DURATION_SECONDS`, `MAX_VIDEO_NOTE_SIZE`, `MAX_VIDEO_NOTE_DURATION_SECONDS` в config;
   - на upload request проверяй size;
   - после async processing проверяй duration и переводить attachment в `error`, если лимит нарушен.
3. Metadata processing:
   - проверь `app/chats/commands/attachments/proccess.py`: извлекаются ли duration для audio и width/height/duration для video_note;
   - если нет, добавь без тяжёлых новых зависимостей, если возможно существующими средствами;
   - для video_note проверь квадратность/почти квадратность или явно документируй, что crop делает клиент.
4. DTO/API docs:
   - `AttachmentDTO.attachment_type` должен документировать `voice | video_note`;
   - `SendMessageRequest.message_type` должен документировать `voice | video_note`;
   - `new_message.payload.message_type` и `ws.history.messages[].type` должны принимать новые значения;
   - обнови `api-docs.md` разделы 6.4, 6.5, 7.4 и Flutter-гайд.
5. Tests:
   - upload request voice/video_note success;
   - неверный MIME для явного `attachment_type` отклоняется;
   - превышение size отклоняется;
   - отправка voice/video_note требует корректный attachment;
   - REST/WS DTO содержит новые типы и download-url.

Acceptance criteria:
- Голосовое сообщение проходит полный флоу presign → PUT → confirm → send → get message/download-url.
- Видеокружок проходит тот же флоу и имеет duration/width/height metadata.
- Старые image/video/file вложения не ломаются.
```

---

## Промт 5. Добавить реакции на сообщения с highload-дизайном поверх существующего чата/outbox

```text
Реакции в чатах ещё не реализованы как доменная функциональность. Их нужно добавить с учётом уже существующего outbox, WebSocket delivery и больших чатов.

Текущая база:
- Есть chat module с CQRS, message repository, WS delivery events и outbox.
- Есть `MAX_REACTIONS_PER_MESSAGE` в `ChatConfig`, но нет полноценной модели/API реакций.
- В `app/settings/model/notification.py` есть настройки `push_reactions`/`inapp_reactions`; это не реализация реакций сообщений, но их нужно учесть при будущих уведомлениях.

Что реализовать:
1. Модели и миграции:
   - `message_reactions`: `id`, `chat_id`, `message_id`, `user_id`, `emoji`, `created_at`, `updated_at`, unique constraint по выбранной продуктовой модели (`message_id,user_id` если одна реакция; `message_id,user_id,emoji` если несколько);
   - `message_reaction_counters`: `message_id`, `emoji`, `count`, `updated_at`, unique `(message_id, emoji)`;
   - индексы: `message_id`, `(message_id, emoji)`, `(chat_id, message_id)`, `(user_id, message_id)`.
2. Commands/queries/routes:
   - `PUT /chats/{chat_id}/messages/{message_id}/reactions/{emoji}/` — идемпотентно поставить/заменить;
   - `DELETE /chats/{chat_id}/messages/{message_id}/reactions/{emoji}/` — идемпотентно убрать;
   - `GET /chats/{chat_id}/messages/{message_id}/reactions/` — агрегаты + курсорный список пользователей по emoji только отдельным query, не внутри `MessageDTO`;
   - проверки членства, ban, доступности сообщения и rate limit.
3. Highload counters:
   - запись реакции должна быть O(1);
   - счётчики обновляй атомарно в той же транзакции через upsert/increment/decrement или через отдельный idempotent consumer, но чтение сообщений должно брать готовую read-model;
   - защити counters от отрицательных значений;
   - добавь тест конкурентных PUT/DELETE.
4. DTO:
   - `ReactionSummaryDTO { emoji: string; count: int; reacted_by_me: bool }`;
   - `MessageDTO.reactions: list[ReactionSummaryDTO]`;
   - `MessageDTO.my_reactions` добавляй только если продуктово разрешено несколько реакций; иначе достаточно `reacted_by_me` внутри summaries;
   - не вкладывай полный список пользователей в каждое сообщение.
5. WebSocket/outbox:
   - доменное событие `chats.message.reaction_updated` через существующий outbox;
   - WS событие `message_reaction_updated` с лёгким payload `{ chat_id, message_id, emoji, count, changed_by, op }`;
   - для supergroup/channel добавь coalescing/debounce или документированную стратегию fan-out ограничения, чтобы 1000 кликов не превращались в 1000 тяжёлых payload-ов.
6. API docs:
   - обнови `api-docs.md`: endpoints, DTO, ошибки, WS event, Flutter optimistic UI/reconciliation;
   - опиши, что агрегаты могут быть eventually consistent, если выбрана асинхронная counter read-model.
7. Tests:
   - идемпотентный PUT;
   - идемпотентный DELETE;
   - смена реакции корректно меняет два counters;
   - конкурентные операции не ломают count;
   - список сообщений отдаёт summaries без N+1;
   - WS payload lightweight;
   - permissions/rate-limit.

Acceptance criteria:
- Реакции работают через REST и обновляют `MessageDTO`.
- Счётчики корректны под конкурентной нагрузкой.
- WebSocket событие лёгкое и совместимо с текущим delivery router/outbox.
- Уведомления о реакциях в будущем могут опираться на settings `push_reactions`/`inapp_reactions`.
```

---

## Рекомендуемый порядок доработок

1. Сначала стабилизировать уже существующий Outbox/Debezium и idempotency consumers.
2. Затем исправить текущую chat profile projection (`avatars`, revision/event_id, consumer payload, backfill).
3. Потом реально подключить profile DTO к REST/WS ответам без N+1.
4. После этого завершить end-to-end voice/video-note flow поверх уже добавленных attachment types.
5. В конце добавить реакции, используя готовый outbox и delivery pipeline.
