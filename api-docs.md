# API Documentation — Full Frontend Reference

## Оглавление
1. [Общее](#общее)
2. [Аутентификация](#аутентификация)
3. [Пользователи](#пользователи)
4. [Профили](#профили)
5. [Проекты](#проекты)
6. [Позиции](#позиции)
7. [Заявки](#заявки)
8. [Роли и права](#роли-и-права)
9. [Сессии](#сессии)
10. [Чаты](#чаты)
11. [WebSocket](#websocket)
12. [Пагинация](#пагинация)
13. [Формат ошибок](#формат-ошибок)
14. [Типы и перечисления](#типы-и-перечисления)

---

## Общее

### Base URL
```
/api/v1
```

### Аутентификация запросов
Все защищённые эндпоинты (помечены 🔒) требуют заголовок:
```
Authorization: Bearer <access_token>
```

### Форматы ID
| Сущность | Тип ID |
|----------|--------|
| User | integer |
| Project | integer |
| Session | integer |
| Profile | integer |
| Chat | integer |
| Message | integer |
| Position | UUID (string) |
| Application | UUID (string) |

---

## Аутентификация

### POST `/auth/login`
Логин по логину/паролю.

**Request** (form-data):
```
username: string
password: string
```

**Response 200:**
```json
{
  "access_token": "eyJ..."
}
```
Refresh token устанавливается в cookie `refresh_token` (httpOnly).

**Ошибки:** `WRONG_LOGIN_DATA` 400

---

### POST `/auth/refresh`
Обновить access token. Берёт refresh token из cookie `refresh_token`.

**Response 200:**
```json
{
  "access_token": "eyJ..."
}
```

**Ошибки:** `INVALID_TOKEN` 403, `EXPIRED_TOKEN` 400

---

### POST `/auth/logout`
Выход — инвалидирует текущий refresh token.

**Response 200:** `{}`

---

### POST `/auth/verifications/email`
Отправить письмо с кодом верификации на email текущего пользователя. 🔒  
Лимит: 3 запроса в час.

**Response 200:** `{}`

---

### POST `/auth/verifications/email/verify`
Подтвердить email по токену из письма.

**Request:**
```json
{
  "token": "string"
}
```

**Response 200:** `{}`

**Ошибки:** `INVALID_TOKEN` 403

---

### POST `/auth/password-resets`
Отправить письмо со ссылкой сброса пароля.  
Лимит: 3 запроса в час.

**Request:**
```json
{
  "email": "string"
}
```

**Response 200:** `{}`

---

### POST `/auth/password-resets/confirm`
Установить новый пароль.

**Request:**
```json
{
  "token": "string",
  "password": "string",
  "password_repeat": "string"
}
```

**Response 200:** `{}`

**Ошибки:** `INVALID_TOKEN` 403, `PASSWORD_MISMATCH` 400

---

### GET `/auth/oauth/{provider}/authorize`
Получить URL для редиректа на OAuth-провайдера (Google, GitHub и т.п.).

**Response 307:** редирект на страницу авторизации провайдера.

**Ошибки:** `NOT_EXIST_PROVIDER_OAUTH` 400

---

### GET `/auth/oauth/{provider}/authorize/connect` 🔒
Привязать OAuth-аккаунт к текущему пользователю.

**Response 307:** редирект на страницу авторизации провайдера.

**Ошибки:** `NOT_EXIST_PROVIDER_OAUTH` 400

---

### GET `/auth/oauth/{provider}/callback`
Callback от OAuth-провайдера (обрабатывается автоматически).

**Response 200:**
```json
{
  "access_token": "eyJ..."
}
```

**Ошибки:** `LINKED_ANOTHER_USER_OAUTH` 409, `OAUTH_STATE_NOT_FOUND` 404

---

## Пользователи

### POST `/users/register`
Регистрация нового пользователя.

**Request:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "password_repeat": "string"
}
```
- `username`: 4–100 символов, только `a-zA-Z0-9 ,.'- `
- `password`: 8–128 символов

**Response 201 — UserResponse:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "user@example.com"
}
```

**Ошибки:** `DUPLICATE_USER` 409, `PASSWORD_MISMATCH` 400, `VALIDATION_EXCEPTION` 422

---

### GET `/users/me` 🔒
Данные текущего пользователя.

**Response 200 — UserDTO:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "user@example.com",
  "is_active": true,
  "is_verified": false,
  "roles": ["member"],
  "permissions": ["read:profile"],
  "sessions": []
}
```

---

### GET `/users/` 🔒
Список пользователей с фильтрами.

**Query params:**
```
email: string (partial match)
username: string (partial match)
is_active: boolean
is_verified: boolean
role_names: string[] (повторяющийся параметр: role_names=admin&role_names=member)
page: integer (default 1)
page_size: integer (1–100, default 20)
sort: string (пример: created_at:desc)
```

**Response 200 — PageResult\<UserDTO\>:**
```json
{
  "items": [{ ...UserDTO }],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### GET `/users/sessions` 🔒
Активные сессии текущего пользователя.

**Response 200:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### POST `/users/{user_id}/roles` 🔒
Назначить роль пользователю. Требует права администратора.

**Request:**
```json
{
  "role_name": "admin"
}
```

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_USER` 404, `NOT_FOUND_ROLE` 404

---

### DELETE `/users/{user_id}/roles/{role_name}` 🔒
Снять роль с пользователя.

**Response 204**

**Ошибки:** `NOT_FOUND_USER` 404, `NOT_FOUND_ROLE` 404

---

### POST `/users/{user_id}/permissions` 🔒
Добавить permissions пользователю напрямую (override).

**Request:**
```json
{
  "permissions": ["read:chat", "write:message"]
}
```

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_USER` 404, `NOT_FOUND_PERMISSIONS` 404

---

### DELETE `/users/{user_id}/permissions` 🔒
Удалить permissions у пользователя.

**Request:**
```json
{
  "permissions": ["read:chat"]
}
```

**Response 200:** `{}`

---

## Профили

### POST `/profiles/` 🔒
Создать профиль для текущего пользователя.

**Request:**
```json
{
  "display_name": "John Doe",
  "bio": "Backend developer",
  "skills": ["Python", "FastAPI"],
  "date_birthday": "1990-01-15"
}
```

**Response 201 — ProfileDTO:**
```json
{
  "id": 1,
  "avatars": {
    "small": "https://...",
    "medium": "https://..."
  },
  "specialization": null,
  "display_name": "John Doe",
  "bio": "Backend developer",
  "date_birthday": "1990-01-15",
  "skills": ["Python", "FastAPI"],
  "contacts": []
}
```

---

### GET `/profiles/`
Список профилей.

**Query params:**
```
display_name: string (partial match)
skills: string[] (повторяющийся параметр)
page: integer
page_size: integer
sort: string
```

**Response 200 — PageResult\<ProfileDTO\>**

---

### GET `/profiles/{id}`
Один профиль.

**Response 200 — ProfileDTO**

**Ошибки:** `NOT_FOUND_PROFILE` 404

---

### PUT `/profiles/{id}` 🔒
Обновить профиль. Только владелец.

**Request:**
```json
{
  "specialization": "Backend Engineer",
  "display_name": "John Doe",
  "bio": "string",
  "skills": ["Python"],
  "date_birthday": "1990-01-15"
}
```
Все поля опциональны.

**Response 200 — ProfileDTO**

**Ошибки:** `NOT_FOUND_PROFILE` 404, `ACCESS_DENIED` 403

---

### POST `/profiles/avatar/presign` 🔒
Получить presigned URL для загрузки аватара напрямую в S3/MinIO.

**Response 200:**
```json
{
  "url": "https://storage.example.com/bucket",
  "fields": {
    "key": "avatars/user_1/avatar.jpg",
    "Content-Type": "image/jpeg",
    "policy": "...",
    "x-amz-signature": "..."
  }
}
```

**Использование:** отправить multipart/form-data POST на `url`, включив все `fields` + файл под ключом `file`.

---

### POST `/profiles/avatar/upload_complete` 🔒
Уведомить сервер об успешной загрузке аватара.

**Response 200:** `{}`

---

### POST `/profiles/{id}/contacts` 🔒
Добавить контакт к профилю.

**Request:**
```json
{
  "provider": "github",
  "contact": "https://github.com/username"
}
```

**Response 201:** `{}`

---

### DELETE `/profiles/{id}/{provide_contact}/delete` 🔒
Удалить контакт из профиля.

**Response 204**

---

## Проекты

### POST `/projects/` 🔒
Создать проект.

**Request:**
```json
{
  "name": "My Project",
  "slug": "my-project",
  "small_description": "Short description",
  "description": "Full description in markdown",
  "visibility": "public",
  "tags": ["python", "web"],
  "meta_data": {}
}
```
- `visibility`: `public | private`

**Response 201 — ProjectDTO:**
```json
{
  "id": 1,
  "owner_id": 1,
  "name": "My Project",
  "slug": "my-project",
  "small_description": "Short description",
  "full_description": "Full description in markdown",
  "visibility": "public",
  "tags": ["python", "web"],
  "meta_data": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "memberships": []
}
```

---

### GET `/projects/` 🔒
Список проектов.

**Query params:**
```
name: string
slug: string
tags: string[] (повторяющийся параметр)
page: integer
page_size: integer
sort: string
```

**Response 200 — PageResult\<ProjectDTO\>**

---

### GET `/projects/my` 🔒
Проекты, в которых текущий пользователь является участником.

**Response 200 — PageResult\<ProjectDTO\>**

---

### GET `/projects/{id}`
Один проект.

**Response 200 — ProjectDTO**

**Ошибки:** `NOT_FOUND_PROJECT` 404

---

### PUT `/projects/{id}` 🔒
Обновить проект. Требует роль owner или admin в проекте.

**Request:** те же поля, что и при создании; все опциональны.

**Response 200 — ProjectDTO**

---

### DELETE `/projects/{id}` 🔒
Удалить проект. Только owner или admin.

**Response 204**

**Ошибки:** `NOT_FOUND_PROJECT` 404, `ACCESS_DENIED` 403

---

### GET `/projects/{id}/positions`
Позиции проекта.

**Response 200 — PageResult\<PositionDTO\>**

---

### POST `/projects/{id}/positions` 🔒
Создать позицию в проекте.

**Request:** см. [Позиции → POST `/positions/`](#позиции)

**Response 201 — PositionDTO**

---

### POST `/projects/{id}/invite` 🔒
Пригласить участника в проект.

**Request:**
```json
{
  "user_id": 5,
  "role_id": 2,
  "permissions_overrides": ["write:positions"]
}
```

**Response 200:** `{}`

---

### POST `/projects/{id}/members/accept` 🔒
Принять приглашение в проект (текущий пользователь).

**Response 200:** `{}`

---

### PUT `/projects/{id}/members/{user_id}/permissions` 🔒
Обновить права конкретного участника.

**Request:**
```json
{
  "permissions_overrides": ["write:positions", "read:applications"]
}
```

**Response 200:** `{}`

---

## Позиции

### GET `/positions/`
Список позиций с фильтрами.

**Query params:**
```
project_id: integer
title: string (partial match)
required_skills: string[] (повторяющийся параметр)
is_open: boolean
location_type: remote | onsite | hybrid
expected_load: low | medium | high
page: integer
page_size: integer
sort: string
```

**Response 200 — PageResult\<PositionDTO\>:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "project_id": 1,
      "title": "Backend Developer",
      "description": "We're looking for...",
      "responsibilities": "You will...",
      "required_skills": ["Python", "PostgreSQL"],
      "is_open": true,
      "location_type": "remote",
      "expected_load": "high"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### GET `/positions/{uuid}`
Одна позиция.

**Response 200 — PositionDTO**

---

### PUT `/positions/{uuid}` 🔒
Обновить позицию.

**Request:** те же поля, что и PositionDTO (все опциональны).

**Response 200 — PositionDTO**

---

### DELETE `/positions/{uuid}` 🔒
Удалить позицию.

**Response 204**

---

### GET `/positions/{uuid}/applications`
Заявки на позицию.

**Response 200 — PageResult\<ApplicationDTO\>**

---

### POST `/positions/{uuid}/applications` 🔒
Подать заявку на позицию.

**Request:**
```json
{
  "message": "I'd like to join because..."
}
```
Поле `message` опционально.

**Response 201 — ApplicationDTO**

---

## Заявки

### GET `/applications/`
Все заявки (для администраторов проектов).

**Query params:**
```
project_id: integer
position_id: UUID
candidate_id: integer
status: pending | accepted | rejected
page: integer
page_size: integer
```

**Response 200 — PageResult\<ApplicationDTO\>:**
```json
{
  "items": [
    {
      "id": "550e8400-...",
      "project_id": 1,
      "position_id": "550e8400-...",
      "candidate_id": 5,
      "status": "pending",
      "message": "I'd like to join...",
      "decided_by": null,
      "decided_at": null
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20
}
```

---

### GET `/applications/me` 🔒
Заявки текущего пользователя.

**Response 200 — PageResult\<ApplicationDTO\>**

---

### POST `/applications/{uuid}/approve` 🔒
Одобрить заявку. Требует права в проекте.

**Response 200 — ApplicationDTO**

---

### POST `/applications/{uuid}/reject` 🔒
Отклонить заявку.

**Response 200 — ApplicationDTO**

---

## Роли и права

### POST `/roles/` 🔒
Создать роль.

**Request:**
```json
{
  "name": "moderator",
  "description": "Can moderate content",
  "security_level": 2,
  "permissions": ["read:chat", "delete:message"]
}
```

**Response 201:** `{}`

**Ошибки:** `DUPLICATE_ROLE` 409, `INVALID_ROLE_NAME` 400

---

### GET `/roles/` 🔒
Список ролей.

**Response 200:**
```json
[
  {
    "name": "admin",
    "description": "Administrator",
    "security_level": 5,
    "permissions": ["read:all", "write:all"]
  }
]
```

---

### POST `/roles/{name}/permissions` 🔒
Добавить permissions к роли.

**Request:**
```json
{
  "permissions": ["delete:message"]
}
```

**Response 200:** `{}`

---

### DELETE `/roles/{name}/permissions` 🔒
Удалить permissions из роли.

**Request:**
```json
{
  "permissions": ["delete:message"]
}
```

**Response 200:** `{}`

---

### GET `/project_roles/`
Список ролей для проектов.

**Response 200:**
```json
[
  {
    "id": 1,
    "name": "owner",
    "permissions": ["write:all"]
  }
]
```

---

### POST `/permissions/` 🔒
Создать permission.

**Request:**
```json
{
  "name": "delete:message"
}
```

**Response 201:** `{}`

---

### GET `/permissions/` 🔒
Список всех permissions.

**Response 200:**
```json
[
  { "name": "read:chat" },
  { "name": "write:message" }
]
```

---

### DELETE `/permissions/{name}` 🔒
Удалить permission.

**Response 204**

**Ошибки:** `PROTECTED_PERMISSION` 409

---

## Сессии

### GET `/sessions/` 🔒
Список сессий (администраторский эндпоинт).

**Query params:**
```
user_id: integer
is_active: boolean
page: integer
page_size: integer
```

**Response 200 — PageResult\<SessionDTO\>:**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### DELETE `/sessions/{id}` 🔒
Завершить сессию (logout конкретного устройства).

**Response 204**

**Ошибки:** `NOT_FOUND_OR_INACTIVE_SESSION` 400

---


## 8) Chats API (`/chats`)

Базовый префикс: `/api/v1/chats`

---

### 8.1 `POST /chats/`
Создать чат.

**Request:**
```json
{
  "chat_type": "direct",
  "member_ids": [5],
  "name": null,
  "description": null,
  "is_public": false
}
```

**Поля:**
- `chat_type`: `direct | group | channel`
- `member_ids`: set пользователей (до 99)
- `name`: до 256
- `description`: до 1024
- `is_public`: boolean

**Response 201:**
```json
{ "chat_id": 42 }
```

**Правила:**
- `direct`: ожидается ровно 1 `member_id` (плюс текущий пользователь)
- `group/channel`: текущий пользователь становится owner

---

### 8.2 `GET /chats/my`
Список чатов пользователя с keyset/cursor пагинацией.

**Query:**
- `limit` (1..100, default 20)
- `cursor` (string | null)

**Response 200 (ChatListCursorPageDTO):**
```json
{
  "items": [
    {
      "id": 42,
      "type": "group",
      "name": "Team",
      "description": "Core chat",
      "avatar_url": null,
      "is_public": false,
      "created_by": 1,
      "last_activity_at": "2026-03-31T10:00:00Z",
      "unread_count": 3,
      "member_count": 5
    }
  ],
  "next_cursor": "...",
  "has_more": true
}
```

---

### 8.3 `GET /chats/{chat_id}`
Детали чата и участники.

**Response 200 (ChatDetailDTO):**
```json
{
  "id": 42,
  "type": "group",
  "name": "Team",
  "description": "Core chat",
  "avatar_url": null,
  "is_public": false,
  "created_by": 1,
  "members": [
    { "user_id": 1, "role_id": 1, "is_muted": false },
    { "user_id": 5, "role_id": 5, "is_muted": false }
  ],
  "unread_count": 0
}
```

---

### 8.4 `PUT /chats/{chat_id}`
Обновить `name`, `description`, `avatar_url`.

**Request:**
```json
{
  "name": "New Name",
  "description": "New Description",
  "avatar_url": "https://..."
}
```

**Response:** `200`

---

### 8.5 Участники чата

#### `POST /chats/{chat_id}/members`
Добавить участника.

**Request:**
```json
{
  "user_id": 7,
  "role_id": 5
}
```

**Response:** `200`

#### `DELETE /chats/{chat_id}/members/{user_id}`
Кик участника.

**Response:** `204`

#### `PUT /chats/{chat_id}/members/{user_id}/role`
Смена роли участника.

**Request:**
```json
{ "role_id": 2 }
```

**Response:** `200`

#### `POST /chats/{chat_id}/members/{user_id}/ban`
Бан/разбан.

**Request:**
```json
{ "ban": true }
```

**Response:** `200`

#### `POST /chats/{chat_id}/leave`
Выйти из чата.

**Response:** `204`

---

### 8.6 Дополнительные данные

#### `GET /chats/{chat_id}/presence`
Онлайн-статусы участников.

**Response 200:**
```json
{
  "chat_id": 42,
  "members": [
    { "user_id": 1, "is_online": true },
    { "user_id": 5, "is_online": false }
  ],
  "online_count": 1
}
```

#### `GET /chats/{chat_id}/messages/{message_id}/delivery`
Кому доставлено сообщение.

**Response 200:**
```json
{
  "message_id": 101,
  "delivered_to": {
    "1": true,
    "5": false
  }
}
```

---

### 8.7 Звонки в чате (LiveKit)

#### `POST /chats/{chat_id}/calls/join`
Вход в звонок и получение токена для LiveKit.

**Response 200 (`JoinTokenDTO`):**
```json
{
  "token": "eyJ...",
  "slug": "chat:42",
  "livekit_url": "wss://livekit.example.com"
}
```

#### `GET /chats/{chat_id}/calls/participants`
Список активно подключённых участников звонка.

**Response 200 (`list[LiveKitParticipantsDTO]`):**
```json
[
  {
    "identity": "1",
    "name": "johndoe",
    "state": 2,
    "joined_at": 1711872000
  }
]
```

#### `PUT /chats/{chat_id}/calls/participants/{user_id}/mute`
Заглушить или разглушить участника.

**Request:**
```json
{ "muted": true }
```

**Response:** `200`

---

## 9) Messages API (`/chats/{chat_id}/messages`)

Базовый префикс: `/api/v1/chats/{chat_id}/messages`

---

### 9.1 Двухшаговая отправка вложений

#### Шаг 1 — `POST /upload`
Запросить upload URL/token для каждого файла.

**Request:**
```json
{
  "uploads": [
    {
      "filename": "photo.png",
      "mime_type": "image/png",
      "file_size": 123456
    }
  ]
}
```

Ограничения:
- `uploads`: 1..11 элементов
- `file_size`: до 100MB на файл

**Response 200:**
```json
[
  {
    "upload_token": "...",
    "upload_url": "https://s3...",
    "attachment_type": "image",
    "expires_in": 300
  }
]
```

#### Шаг 2 — `POST /`
Отправить сообщение с `upload_tokens` (после загрузки файлов в S3).

**Request:**
```json
{
  "content": "Look at this",
  "reply_to_id": null,
  "message_type": "text",
  "upload_tokens": ["token-1"]
}
```

Правила:
- хотя бы одно: `content` или `upload_tokens`
- `content`: до 4096 символов
- `upload_tokens`: до 11

**Response 201 (SendMessageResult):**
```json
{
  "message_id": 120,
  "chat_id": 42,
  "created_at": "2026-03-31T10:10:00Z"
}
```

---

### 9.2 Пересылка сообщений — `POST /forward`

**Request:**
```json
{
  "source_chat_id": 10,
  "source_message_id": 501,
  "comment": "FYI"
}
```

**Response 201 (ForwardMessageResult):**
```json
{
  "message_id": 121,
  "chat_id": 42,
  "created_at": "2026-03-31T10:11:00Z"
}
```

---

### 9.3 Список сообщений — `GET /`

**Query:**
- `limit` (1..100, default 30)
- `before_id` (int | null)

**Response 200 (MessageCursorPage):**
```json
{
  "items": [
    {
      "id": 120,
      "chat_id": 42,
      "author_id": 1,
      "type": "text",
      "content": "hello",
      "reply_to_id": null,
      "media_url": null,
      "is_deleted": false,
      "is_edited": false,
      "created_at": "2026-03-31T10:10:00Z",
      "updated_at": "2026-03-31T10:10:00Z",
      "reply_to": null,
      "attachments": [],
      "forwarded_from_chat_id": null,
      "forwarded_from_message_id": null
    }
  ],
  "next_cursor": 119,
  "has_more": true,
  "read_cursors": {}
}
```

---

### 9.4 URL на скачивание вложения
`GET /{message_id}/attachments/{attachment_id}/url`

**Response 200:**
```json
{
  "attachment_id": "6d0de7a6-94b6-42ba-9005-62f40e7652f6",
  "url": "https://s3...",
  "expires_in": 300
}
```

---

### 9.5 Read details
`GET /read-details`

**Query:**
- `limit` (1..200, default 50)
- `after_user_id` (int | null)

**Response 200:**
```json
{
  "items": [
    { "user_id": 1, "last_read_message_id": 120 },
    { "user_id": 5, "last_read_message_id": 118 }
  ],
  "next_cursor": 5,
  "has_more": false
}
```

---

### 9.6 Редактировать/удалить/прочитать

#### `PUT /{message_id}`
**Request:**
```json
{ "content": "edited text" }
```
**Response:** `200`

#### `DELETE /{message_id}`
**Response:** `204`

#### `POST /read`
**Request:**
```json
{ "message_id": 120 }
```
**Response:** `204`

---

## 10) WebSocket API

### Endpoint
```text
WS /api/v1/chats/ws/?token=<access_token>
```

### Поведение подключения
- Токен валидируется при коннекте
- Если токен невалиден -> закрытие `4001`
- Если превышен лимит подключений пользователя -> закрытие `1008`
- Одно соединение подписывается на каналы всех чатов пользователя

### Формат события
```json
{
  "type": "event_type",
  "chat_id": 42,
  "payload": {},
  "ts": "2026-03-31T10:00:00Z"
}
```

### События от сервера
- `new_message`
- `message_deleted`
- `message_edited`
- `messages_read`
- `member_joined`
- `member_left`
- `member_kick`
- `typing_start`
- `typing_stop`
- `ping`
- `call_started`
- `call_joined`
- `call_left`
- `call_ended`

### События от клиента
Клиент может слать JSON того же формата:

- индикатор набора: `typing_start`
- стоп индикатора: `typing_stop`
- подтверждение доставки: `new_message` + `payload.message_id`

Пример подтверждения доставки:
```json
{
  "type": "new_message",
  "chat_id": 42,
  "payload": {
    "message_id": 120
  }
}
```

---

## 11) LiveKit webhook (server-side integration)

> Этот endpoint обычно не вызывает frontend напрямую, но важно понимать, откуда приходят call-события в чатах.

### `POST /api/v1/livekit/webhook`
- Проверяется подпись webhook
- По событию LiveKit публикуется WS-событие в чат и создаётся system message

Маппинг:
- `room_started` -> `call_started`
- `participant_joined` -> `call_joined`
- `participant_left` -> `call_left`
- `room_finished` -> `call_ended`

**Response 200:**
```json
{ "ok": true }
```

---

## 12) Ошибки и обработка на клиенте

Единый формат ошибки:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable",
    "detail": {}
  },
  "status": 400,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1700000000.123
}
```

### Частые статусы
- `400` — бизнес-ошибка/невалидные данные на уровне домена
- `401/403` — проблемы авторизации/доступа
- `404` — сущность не найдена
- `409` — конфликт
- `422` — валидация входных данных (`VALIDATION`)
- `500` — внутренняя ошибка

### Рекомендованная стратегия на frontend
1. `401/403` на приватных ручках -> попытка `POST /auth/refresh` (1 раз)
2. Если refresh неуспешен -> принудительный logout + редирект на login
3. Для `422` показывать field-level ошибки формы
4. Логировать `request_id` в Sentry/консоль для саппорта

---

## 13) Пагинация (offset и cursor)

### Offset pagination
Используется в большинстве list endpoint.

**Query:**
- `page` (>=1)
- `page_size` (1..100)
- `sort` в формате `field:asc|desc[,field2:asc|desc]`

**Response envelope:**
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### Cursor pagination
Используется в:
- `GET /chats/my` -> `limit`, `cursor`
- `GET /chats/{chat_id}/messages` -> `limit`, `before_id`
- `GET /chats/{chat_id}/messages/read-details` -> `limit`, `after_user_id`

---

## 14) Типы/enum, важные для UI

### ChatType
- `direct`
- `group`
- `channel`

### MessageType
- `text`
- `image`
- `file`
- `system`
- `reply`

### AttachmentType
- `image`
- `video`
- `file`

### WS event types
- `new_message`
- `message_deleted`
- `message_edited`
- `messages_read`
- `member_joined`
- `member_left`
- `member_kick`
- `typing_start`
- `typing_stop`
- `ping`
- `call_started`
- `call_joined`
- `call_left`
- `call_ended`

---


Сейчас для звонков используется чат (`/chats/{chat_id}/calls/*`) + WS + `livekit/webhook`, а не отдельный публичный room REST API.

## Пагинация

Все эндпоинты, возвращающие списки, поддерживают:

**Query params:**
```
page: integer (default 1, min 1)
page_size: integer (default 20, min 1, max 100)
sort: string (формат: field:direction, например created_at:desc,username:asc)
```

**Response envelope:**
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

> **Исключение:** `GET /chats/{chat_id}/messages` использует cursor-based пагинацию — параметры `before_id` и `limit` вместо `page`/`page_size`.

---

## Формат ошибок

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "detail": {}
  },
  "status": 400,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1705315800.123
}
```

### Полный список кодов ошибок

| Code | HTTP Status | Когда возникает |
|------|-------------|-----------------|
| `WRONG_LOGIN_DATA` | 400 | Неверный логин или пароль |
| `INVALID_TOKEN` | 403 | Токен невалиден (подделан или не существует) |
| `EXPIRED_TOKEN` | 400 | Токен истёк |
| `PASSWORD_MISMATCH` | 400 | `password` и `password_repeat` не совпадают |
| `DUPLICATE_USER` | 409 | Пользователь с таким email/username уже существует |
| `DUPLICATE_ROLE` | 409 | Роль с таким именем уже существует |
| `NOT_FOUND_USER` | 404 | Пользователь не найден |
| `NOT_FOUND_ROLE` | 404 | Роль не найдена |
| `NOT_FOUND_PERMISSIONS` | 404 | Один или несколько permissions не найдены |
| `NOT_FOUND_PROFILE` | 404 | Профиль не найден |
| `NOT_FOUND_PROJECT` | 404 | Проект не найден |
| `NOT_FOUND_OR_INACTIVE_SESSION` | 400 | Сессия не найдена или уже завершена |
| `NOT_FOUND_CHAT` | 404 | Чат не найден |
| `NOT_FOUND_MESSAGE` | 404 | Сообщение не найдено |
| `NOT_CHAT_MEMBER` | 403 | Пользователь не является участником чата |
| `CHAT_ACCESS_DENIED` | 403 | Недостаточно прав в чате (нужна роль выше) |
| `ALREADY_CHAT_MEMBER` | 409 | Пользователь уже состоит в этом чате |
| `DIRECT_CHAT_EXISTS` | 409 | Direct-чат с этим пользователем уже существует |
| `MEMBER_LIMIT_EXCEEDED` | 400 | Достигнут лимит участников чата (100) |
| `MESSAGE_TOO_LONG` | 400 | Сообщение превышает 4096 символов |
| `ACCESS_DENIED` | 403 | Нет системных прав (detail содержит нужные permissions) |
| `PROTECTED_PERMISSION` | 409 | Permission защищён от изменения или удаления |
| `LINKED_ANOTHER_USER_OAUTH` | 409 | OAuth-аккаунт уже привязан к другому пользователю |
| `OAUTH_STATE_NOT_FOUND` | 404 | OAuth state устарел или не существует |
| `NOT_EXIST_PROVIDER_OAUTH` | 400 | Провайдер OAuth не поддерживается |
| `INVALID_ROLE_NAME` | 400 | Имя роли содержит недопустимые символы |
| `VALIDATION_EXCEPTION` | 422 | Ошибка валидации входных данных |
| `INTERNAL_EXCEPTION` | 500 / 503 | Внутренняя ошибка сервера |

> При ошибке `VALIDATION_EXCEPTION` поле `detail` содержит массив:
> ```json
> [{ "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email" }]
> ```

---

## Типы и перечисления

### ChatType
```
direct   — личный чат (2 участника, создаётся один раз)
group    — групповой чат (до 100 участников)
channel  — канал (только владелец/admin пишут) НЕРЕАЛИЗОВАНО
```

### MemberRole (роли в чате)
```
owner   — создатель, все права
admin   — управление участниками, редактирование чата
member  — чтение и отправка сообщений
viewer  — только чтение
```

**Матрица прав участников чата:**

| Действие | viewer | member | admin | owner |
|----------|--------|--------|-------|-------|
| Читать сообщения | ✓ | ✓ | ✓ | ✓ |
| Отправлять сообщения | — | ✓ | ✓ | ✓ |
| Редактировать своё сообщение | — | ✓ | ✓ | ✓ |
| Удалять своё сообщение | — | ✓ | ✓ | ✓ |
| Удалять любое сообщение | — | — | ✓ | ✓ |
| Закреплять сообщения | — | — | ✓ | ✓ |
| Добавлять участников | — | — | ✓ | ✓ |
| Удалять участников | — | — | ✓ | ✓ |
| Банить участников | — | — | ✓ | ✓ |
| Редактировать чат (название/описание) | — | — | ✓ | ✓ |
| Удалить чат | — | — | — | ✓ |
| Менять роли участников | — | — | — | ✓ |

### MessageType
```
text    — обычное текстовое сообщение
image   — изображение (content = подпись, media_url = ссылка) НЕРЕАЛИЗОВАНО
file    — файл (content = имя файла, media_url = ссылка) НЕРЕАЛИЗОВАНО
reply   — ответ на сообщение (reply_to_id обязателен)
system  — системное сообщение (автоматическое, не от пользователя)
```

### LocationType (для позиций)
```
remote   — удалённая работа
onsite   — в офисе
hybrid   — гибридный формат
```

### ExpectedLoad (для позиций)
```
low      — частичная занятость
medium   — средняя нагрузка
high     — полная занятость
```

### ApplicationStatus
```
pending   — ожидает рассмотрения
accepted  — принята
rejected  — отклонена
```

### ProjectVisibility
```
public   — виден всем
private  — только участникам
```