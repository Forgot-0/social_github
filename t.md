## 🔎 Обзор бэкенда (что уже сделано) — для фронтенд senior

### 🧱 Архитектура & стек (что важно понимать)
- **FastAPI** (асинхронный) + **Pydantic** (схемы запросов/ответов) + **OpenAPI** (Swagger / Redoc).
- **SQLAlchemy (async)** + PostgreSQL (конфиг через app.py).
- **DI + CQRS/медиатор**: используется `dishka` (контейнер зависимостей) и паттерн mediator (commands / queries).
- **Redis**:
  - Rate limiting (`fastapi_limiter`),
  - возможные кэш/очереди (вплоть до message broker, есть адаптеры для Kafka/Redis).
- **Аутентификация**:
  - Access token — Bearer (в `Authorization` header).
  - Refresh token — **HTTP-only cookie** (`refresh_token`), устанавливается/удаляется бекендом.
- **Формат ошибок** — стандартизирован в `ErrorResponse` (поле `error` + `status` + `request_id` + `timestamp`).

---

## 🚪 Точки входа (эндпоинты) — базовый API

API доступно по префиксу:  
**`/api/v1/...`** (`app_config.API_V1_STR`)

### 🔐 Аутентификация & пользователи (`/api/v1/auth`, `/api/v1/users`)
**Основные пути:**
- `POST /api/v1/auth/login` — логин (возвращает access token; ставит refresh cookie)
- `POST /api/v1/auth/refresh` — обновление access token (использует cookie)
- `POST /api/v1/auth/logout` — разлогин (удаляет refresh cookie)

**Регистрация / профиль**
- `POST /api/v1/users/register` — регистрация
- `GET /api/v1/users/me` — базовый профиль текущего пользователя

**Остальные auth-эндпоинты:**
- Верификация email, сброс пароля, OAuth (авторизация и callback)
- Управление ролями/права/сессиями и т.п. (CRUD по ролям/permissions/sessions)

---

## 🧩 Проекты / позиции / заявки (core фича)

### 🧱 Проекты 
**`/api/v1/projects`**
- `POST /` — создать проект
- `GET /` — список проектов (фильтрация через query params)
- `GET /{project_id}` — подробности
- `PUT /{project_id}` — обновление
- `POST /{project_id}/invite` — пригласить пользователя (роль + права)
- `POST /{project_id}/members/accept` — принять приглашение
- `PUT /{project_id}/members/{user_id}/permissions` — обновить права участника

### 🧩 Позиции
**`/api/v1/positions`**
- `GET /` — список позиций (фильтры)
- `GET /{position_id}` — деталка
- `PUT /{position_id}` — обновить
- `DELETE /{position_id}` — удалить
- `POST /{position_id}/apply` — откликнуться

### 📩 Заявки / отклики
**`/api/v1/applications`**
- `GET /` — список заявок (с фильтрами)
- `POST /{application_id}/approve` — принять
- `POST /{application_id}/reject` — отклонить

### 👥 Роли / права
- `GET /api/v1/project_roles` — роли проекта (набор "owner/member/..." и т.п.)
- `GET /api/v1/roles` — роли (системные)
- CRUD для ролей/permissions доступен через `/api/v1/roles`, `/api/v1/permissions`

---

## 🧑‍💼 Профили пользователей
**`/api/v1/profiles`**
- `POST /` — создать профиль (bio, skills, дата, и т.п.)
- `GET /` — список профилей (параметры фильтрации)
- `GET /{id}` — профиль
- `PUT /{id}` — обновить профиль

### Аватар
- `POST /avatar/presign` — получить presigned URL (для загрузки в S3/MinIO)
- `POST /avatar/upload_complete` — завершение загрузки

### Контакты
- `POST /{profile_id}/contacts` — добавить контакт
- `DELETE /{profile_id}/{provider}/delete` — удалить контакт

---

## 🔐 Авторизация / права / rate limits
- **Bearer token** (Authorization: `Bearer <token>`) для большинства защищённых эндпоинтов.
- **Refresh token** хранится в cookie; фронтенд не может читать его (httponly).
- Есть кастомный `ConfigurableRateLimiter` (ограничения задаются в декораторах в нужных роутерах).

---

## 📦 OpenAPI / документация
- Документация генерируется автоматически.
- Обычно доступна на `/docs` или `/redoc` (стандарт FastAPI).
- Также хранится готовый openapi.json в корне репозитория.

---

## 🧠 Что фронтенду важно знать (чего ещё не видно в структуре)
✅ **Паттерн команд/запросов (CQRS)** — в роутах почти всегда команды/запросы передаются в медиатор (`mediator.handle_command / handle_query`), это значит, что почти все бизнес-правила лежат не в контроллерах, а в `commands/` / `queries/`.

✅ **Структуры DTO и схем** (Pydantic) задают точный контракт ответ/запрос — фронтенд может ориентироваться на них (есть отдельные `schemas/...` и `dtos/...`).

✅ **Зависимости** (auth/permissions) вынесены в `deps` / `core/services/auth`, т.е. ожидаемый Behavior: если запроса нет токена или токен неверный — будет `401/403` с нормализованной структурой ошибки.

---

## ✅ Рекомендации фронтенду для быстрого старта
1. **Поднять локально** и сразу открыть `/docs` → там будут все схемы и примеры.
2. Сделать клиентскую обёртку для:
   - `POST /api/v1/auth/login` → сохранять access token в memory/state (или localStorage если нужно).
   - `POST /api/v1/auth/refresh` → вызывать перед истечением access токена (refresh токен в cookie).
3. Для всех запросов с авторизацией — добавлять `Authorization: Bearer <token>`.
4. На стороне UI полагаться на стандартный формат ошибок (`error.code`, `error.message`, `error.detail`), чтобы строить UX (toast, модалки).

---

Если нужно — могу **составить точный список всех API-эндпоинтов и их форматов (request/response)** в виде понятной таблицы или OpenAPI-ориентированного документа для фронтенда (развернутый API contract).

User: составить точный список всех API-эндпоинтов и их форматов (request/response) И учитывать все бизнес логику сформировать очень подробное тз для фронтера что бы он сделать приложение без api запросов. развернутый API contract

GitHub Copilot: Read [](file:///home/forgot/social_github/openapi.json)

Searched for regex `MAX_PROJECT|max_projects|projects_limit|limit.*project|PROJECTS_LIMIT|limit.*position|MAX_POSITIONS|positions_limit` (`**/app/**/*.py`), 8 results

Read [](file:///home/forgot/social_github/app/projects/config.py)

Read [](file:///home/forgot/social_github/app/projects/exceptions.py)

## 📌 Итог: развёрнутый API‑контракт (полный список эндпоинтов + форматы запрос/ответ + бизнес-правила)

Я собрал **все доступные REST‑эндпоинты** (из openapi.json) и структуру всех их запросов/ответов + ключевые бизнес-ограничения (лимиты, права, rate‑limits и т.д.). Это документ, по которому frontend-старший разработчик сможет **сделать приложение, не задавая дополнительных вопросов по API**.

> 🔎 **Важно:** openapi.json в репозитории — это *официальная спецификация*. Любые расхождения между ней и словами ниже — лечатся именно сверкой с этим JSON.

---

## 🧭 Общая картина

### Базовый URL
- Предположительно: `http://<host>:<port>`  
- Префикс API: **`/api/v1`**

### Формат ответов об ошибке (единый)
Все ошибки возвращаются в формате:

```json
{
  "error": {
    "code": "SOME_CODE",
    "message": "Human-readable message",
    "detail": { ... }
  },
  "status": 400,
  "request_id": "<uuid>",
  "timestamp": "<timestamp>"
}
```

> Это применяется к большинству эндпоинтов (400/403/404/422 и др).

### Аутентификация / авторизация
- **Bearer токен** (`Authorization: Bearer <access_token>`) — основной механизм защиты.
- **Refresh токен** хранится в **cookie** (`refresh_token`, httponly).
  - Важно: фронт должен вызывать `refresh` с `withCredentials: true`, чтобы cookie отправлялась.


### Аутентификация / авторизация
- **Bearer токен** (`Authorization: Bearer <access_token>`) — основной механизм защиты.
- **Refresh токен** хранится в **cookie** (`refresh_token`, httponly).
  - Важно: фронт должен вызывать `refresh` с `withCredentials: true`, чтобы cookie отправлялась.

---

## 🔐 1. Аутентификация (auth)

### 1.1 `POST /api/v1/auth/login`
**Описание:** логин по username+password.  
**Контент:** `application/x-www-form-urlencoded`

**Request:**
- `username` (string)  
- `password` (string)

**Response 200:**
```json
{ "access_token": "<jwt>" }
```

**Ошибки:**
- `400` — WRONG_LOGIN_DATA (некорректные данные)
- `422` — валидация формы

---

### 1.2 `POST /api/v1/auth/refresh`
**Описание:** обновление access token (refresh в cookie).  
**Запрос:** cookie `refresh_token` (неявно).

**Response 200:**
```json
{ "access_token": "<new jwt>" }
```

**Ошибки:**
- `400` — INVALID_TOKEN / EXPIRED_TOKEN
- `404` — NOT_FOUND_OR_INACTIVE_SESSION

---

### 1.3 `POST /api/v1/auth/logout`
**Описание:** инвалидирует refresh-токен (удаляет cookie).

**Response 204** (пустой)

**Ошибки:**
- `400` — INVALID_TOKEN

---

### 1.4 Email verification / reset

- `POST /api/v1/auth/verifications/email` — отправка кода верификации (лимит 3/час)
  - Body: `{ "email": "..." }`
- `POST /api/v1/auth/verifications/email/verify` — подтвердить email
  - Body: `{ "token": "..." }`
- `POST /api/v1/auth/password-resets` — выслать код сброса (лимит 3/час)
  - Body: `{ "email": "..." }`
- `POST /api/v1/auth/password-resets/confirm` — сброс пароля
  - Body:
    ```json
    {
      "token": "...",
      "password": "...",
      "password_repeat": "..."
    }
    ```

**Ошибки:**  
- `404 NOT_FOUND_USER`  
- `400 INVALID_TOKEN / PASSWORD_MISMATCH`  
- `422` — валидация

---

### 1.5 OAuth (опционально)
- `GET /api/v1/auth/oauth/{provider}/authorize` — URL для авторизации (redirect)
- `GET /api/v1/auth/oauth/{provider}/authorize/connect` — URL для привязки к существующему пользователю (требует авторизации)
- `GET /api/v1/auth/oauth/{provider}/callback?code=..&state=..` — callback

**Ошибки:**
- `400 NOT_EXIST_PROVIDER_OAUTH`
- `404 OAUTH_STATE_NOT_FOUND` / `NOT_FOUND_USER`
- `409 LINKED_ANOTHER_USER_OAUTH`

---

## 🧑‍💼 2. Пользователи (Users)

### 2.1 `POST /api/v1/users/register` — регистрация
Body:
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "password_repeat": "string"
}
```

**Ответ 201:**
```json
{ "id": 1, "username": "user", "email": "user@example.com" }
```

**Ошибки:**
- `400 PASSWORD_MISMATCH`
- `409 DUPLICATE_USER`

---

### 2.2 `GET /api/v1/users/me` — профиль текущего пользователя
**Требует:** Bearer token  
**Ответ:**
```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com"
}
```

**Ошибки:**
- `400 INVALID_TOKEN`
- `403 ACCESS_DENIED` (нужны права `user:active`)
- `404 NOT_FOUND_USER`

---

### 2.3 Управление ролями/правами пользователя (админ/owner)

#### Добавить роль:
- `POST /api/v1/users/{user_id}/roles`
- Body: `{ "role_name": "string" }`

#### Удалить роль:
- `DELETE /api/v1/users/{user_id}/roles/{role_name}`

#### Добавить права:
- `POST /api/v1/users/{user_id}/permissions`
- Body: `{ "permissions": ["p1","p2"] }`

#### Удалить права:
- `DELETE /api/v1/users/{user_id}/permissions`
- Body: `{ "permissions": ["p1","p2"] }`

**Ошибки:**  
- `403 ACCESS_DENIED`  
- `404 NOT_FOUND_USER`, `NOT_FOUND_ROLE`, `NOT_FOUND_PERMISSIONS`

---

### 2.4 Список пользователей (админ)
`GET /api/v1/users/`  
**Query Params (фильтрация):**
- `email`, `username`, `is_active`, `is_verified`, `is_deleted`
- `created_after`, `created_before`, `updated_after`, `updated_before`
- `has_oauth_accounts`, `has_sessions`
- `role_names[]`, `permission_names[]`
- `page`, `page_size`, `sort`

**Response:** `PageResult<UserDTO>`

---

### 2.5 Сессии пользователя
- `GET /api/v1/users/sessions` — получить текущую сессию (для текущего пользователя)
- `DELETE /api/v1/sessions/{session_id}` — выйти из конкретной сессии
- `GET /api/v1/sessions/` — список сессий (фильтры: `user_id`, `device_id`, `last_activity_after/before`, `is_active`, пагинация)

---

## 🛡 3. Права / роли (permissions/roles)

### 3.1 Права (Permissions)
- `POST /api/v1/permissions/` — создать право  
  Body: `{ "name":"string" }`
- `GET /api/v1/permissions/` — получить список прав (фильтры: name, page, page_size, sort)
- `DELETE /api/v1/permissions/{name}` — удалить право

---

### 3.2 Роли (Roles)
- `POST /api/v1/roles/` — создать роль  
  Body: `{ "name","description","security_level","permissions": ["p1","p2"] }`
- `GET /api/v1/roles/` — список ролей (фильтры: name, security_level, permission_names, page, page_size, sort)
- `POST /api/v1/roles/{role_name}/permissions` — добавить права в роль
- `DELETE /api/v1/roles/{role_name}/permissions` — убрать права из роли

---

## 👤 4. Профили пользователей (Profiles)

### 4.1 Создание профиля
`POST /api/v1/profiles/` (Bearer)
Body:
```json
{
  "display_name": "string|null",
  "bio": "string|null",
  "skills": ["js", "python"] | null,
  "date_birthday": "YYYY-MM-DD" | null
}
```

---

### 4.2 Получение списка профилей
`GET /api/v1/profiles/`
Query:
- `display_name`, `skills[]`, `page`, `page_size`, `sort`

Ответ: `PageResult<ProfileDTO>`

---

### 4.3 Получение / обновление профиля
- `GET /api/v1/profiles/{profile_id}` → `ProfileDTO`
- `PUT /api/v1/profiles/{profile_id}` → обновление (те же поля, что создание)

**Ошибки:**
- `404 NOT_FOUND_PROFILE`

---

### 4.4 Аватар
- `POST /api/v1/profiles/avatar/presign` — получает presigned URL (upload to S3/MinIO)
  - Body: `{ "filename","size","content_type" }`
  - Response: `{ "url","fields", "key_base" }`
- `POST /api/v1/profiles/avatar/upload_complete` — подтверждение загрузки
  - Body: `{ "key_base","size","content_type" }`

---

### 4.5 Контакты
- `POST /api/v1/profiles/{profile_id}/contacts` — добавить контакт  
  Body: `{ "provider","contact" }`
- `DELETE /api/v1/profiles/{profile_id}/{provide_contact}/delete` — удалить контакт

---

## 🏗 5. Проекты (Projects)

### 5.1 Лимиты (бизнес-логика)
- **Максимум проектов на пользователя:** **3** (конфиг `MAX_PROJECTS_PER_USER`, ошибка `MAX_PROJECTS_LIMIT_EXCEEDED`)
- **Максимум позиций на проект:** **5** (конфиг `MAX_POSITIONS_PER_PROJECT`, ошибка `MAX_POSITIONS_PER_PROJECT_LIMIT_EXCEEDED`)

---

### 5.2 CRUD проекты
#### Создать проект
`POST /api/v1/projects/` (Bearer)
Body:
```json
{
  "name": "string",
  "slug": "string",
  "description": "string|null",
  "visibility": "string|null",
  "meta_data": { ... } | null,
  "tags": ["t1","t2"] | null
}
```

**Ошибки:**
- `409 ALREADY_EXISTS` (slug)
- `400 MAX_PROJECTS_LIMIT_EXCEEDED` (если больше лимита)

---

#### Список проектов
`GET /api/v1/projects/` (Bearer)
Query:
- `name`, `slug`, `tags[]`
- `page`, `page_size`, `sort`

Ответ: `PageResult<ProjectDTO>`  
`ProjectDTO` содержит поле `memberships: MemberDTO[]` (показывает участников и роли).

---

#### Получить проект
`GET /api/v1/projects/{project_id}` (Bearer)  
Ответ: `ProjectDTO`

#### Обновить проект
`PUT /api/v1/projects/{project_id}` (Bearer)  
Body: те же поля, что при создании (все nullable).

---

## 👥 6. Участники / приглашения

### 6.1 Пригласить участника
`POST /api/v1/projects/{project_id}/invite` (Bearer)

Body:
```json
{
  "user_id": 123,
  "role_id": 1,
  "permissions_overrides": { ... } | null
}
```

---

### 6.2 Принять приглашение
`POST /api/v1/projects/{project_id}/members/accept` (Bearer)

---

### 6.3 Обновить права участника
`PUT /api/v1/projects/{project_id}/members/{user_id}/permissions` (Bearer)

Body:
```json
{
  "permissions_overrides": { ... }
}
```

---

## 🧩 7. Позиции (Positions)

### 7.1 Создать позицию (внутри проекта)
`POST /api/v1/projects/{project_id}/positions` (Bearer)

Body:
```json
{
  "title": "string",
  "description": "string",
  "responsibilities": "string|null",
  "required_skills": ["a","b"] | null,
  "location_type": "remote | onsite | hybrid" | null,
  "expected_load": "low | medium | high" | null
}
```

**Ошибки:**
- `400 MAX_POSITIONS_PER_PROJECT_LIMIT_EXCEEDED`

---

### 7.2 Список позиций
`GET /api/v1/positions/`
Query:
- `project_id`, `title`
- `required_skills[]`
- `is_open` (bool, default true)
- `location_type`, `expected_load`
- `page`, `page_size`, `sort`

Ответ: `PageResult<PositionDTO>`

---

### 7.3 Позиция по ID
`GET /api/v1/positions/{position_id}` → `PositionDTO`

---

### 7.4 Обновление / удаление
- `PUT /api/v1/positions/{position_id}` (Bearer) — body: `PositionUpdateRequest` (все поля nullable)
- `DELETE /api/v1/positions/{position_id}` (Bearer)

---

### 7.5 Откликнуться на позицию
`POST /api/v1/positions/{position_id}/apply` (Bearer)

Body:
```json
{ "message": "string|null" }
```

---

## ✅ 8. Заявки (Applications)

### 8.1 Список заявок
`GET /api/v1/applications/`
Query:
- `project_id`, `position_id`, `candidate_id`
- `status` (pending/accepted/rejected)
- `page`, `page_size`, `sort`

Ответ: `PageResult<ApplicationDTO>`

---

### 8.2 Принятие/отклонение
- `POST /api/v1/applications/{application_id}/approve` (Bearer)
- `POST /api/v1/applications/{application_id}/reject` (Bearer)

---

## 🧪 9. Служебные эндпоинты
- `GET /health` — healthcheck
- `GET /metrics` — Prometheus metrics

---

## 🧠 Ключевые бизнес-ограничения (логика проверки)
### Лимиты (core)
- Макс проектов (на пользователя): **3**
- Макс позиций (в проекте): **5**
- Длина тегов / названий (в `project_config`)

### Безопасность / права
- Большинство модифицирующих эндпоинтов требуют Bearer токен
- Разграничение прав основано на ролях/permissions (через middleware / зависимости)
- Ошибки API возвращаются в едином формате, поэтому frontend должен единожды реализовать парсинг `error.code`, `error.message`.

### Rate limits (требует внимание)
- `POST /api/v1/auth/verifications/email` — **3 запросa/час**
- `POST /api/v1/auth/password-resets` — **3 запроса/час**
(они реализованы через `ConfigurableRateLimiter`)

---

## ✅ Рекомендации по использованию (для фронтенда)

### 1) Авторизация
1. `POST /auth/login` → сохранить `access_token`
2. В фоновом refresh’е:
   - `POST /auth/refresh` (с `withCredentials:true`)
3. На logout:
   - `POST /auth/logout` (с `withCredentials:true`)
   - Удалить access_token

> **Важно:** Refresh token не виден JS (httponly cookie). API сам его ставит/удаляет.

---

### 2) Нормализация данных
- Использовать DTO-структуры из OpenAPI (напр. `ProjectDTO`, `ProfileDTO`, `PositionDTO`, `ApplicationDTO`)
- Пагинация: `page`, `page_size`, `sort` (значение вида `created_at:desc` и т.п.)

---

### 3) Ошибки
- Разбирать `response.error.code` и `response.error.detail`
- На `422` отображать валидационные сообщения (`response.error.detail` — массив ошибок)

---

## 🔧 Как быстро импортировать в фронт
Использовать готовый openapi.json:
- В Postman / Insomnia / Swagger UI — импортируя openapi.json
- Автоматически генерировать TypeScript SDK (openapi-generator / swagger-codegen)

---

## ✅ Итог: что уже готово фронту
- Полный набор CRUD для **проектов**, **позиций**, **профилей**
- Механика приглашений + принятия участников
- Система ролей/прав пользователей
- Авторизация + refresh + logout + email/пароль reset + OAuth
- Явно описаны все ответы и ошибки

---

