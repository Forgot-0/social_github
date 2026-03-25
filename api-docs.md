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

## Чаты

### POST `/chats/` 🔒
Создать чат — direct (1:1) или группу.

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

| Поле | Тип | Описание |
|------|-----|----------|
| `chat_type` | `direct \| group \| channel` | Тип чата |
| `member_ids` | `integer[]` | Для `direct` — ровно 1 ID; для `group` — до 99 ID |
| `name` | `string \| null` | Название (обязательно для group/channel) |
| `description` | `string \| null` | Описание |
| `is_public` | `boolean` | Публичная группа (можно найти) |

**Response 201:**
```json
{
  "chat_id": 42
}
```

**Ошибки:** `DIRECT_CHAT_EXISTS` 409, `MEMBER_LIMIT_EXCEEDED` 400

---

### GET `/chats/my` 🔒
Список чатов текущего пользователя, отсортированных по активности. Использует keyset-пагинацию.

**Query params:**
```
limit: integer (1–100, default 20)
cursor: string | null — курсор для следующей страницы (из поля next_cursor предыдущего ответа)
```

**Response 200 — ChatListCursorPageDTO:**
```json
{
  "items": [
    {
      "id": 42,
      "type": "direct",
      "name": null,
      "description": null,
      "avatar_url": null,
      "is_public": false,
      "created_by": 1,
      "last_activity_at": "2024-01-15T10:30:00Z",
      "unread_count": 3,
      "member_count": 2
    }
  ],
  "next_cursor": "base64encodedstring",
  "has_more": true
}
```

**Паттерн загрузки:**
```
// Первая загрузка
GET /chats/my?limit=20

// Следующая страница
GET /chats/my?limit=20&cursor={next_cursor из предыдущего ответа}
```

---

### GET `/chats/{chat_id}` 🔒
Детальная информация о чате со списком участников.

**Response 200 — ChatDetailDTO:**
```json
{
  "id": 42,
  "type": "group",
  "name": "Team Chat",
  "description": "Our team channel",
  "avatar_url": "https://...",
  "is_public": false,
  "created_by": 1,
  "members": [
    {
      "user_id": 1,
      "role_id": 1,
      "is_muted": false
    },
    {
      "user_id": 5,
      "role_id": 5,
      "is_muted": false
    }
  ],
  "unread_count": 0
}
```

> `role_id` соответствует ID роли из системы чат-ролей: 1 — owner, 2 — admin, 4 — direct, 5 — member, 6 — viewer.

**Ошибки:** `NOT_FOUND_CHAT` 404, `NOT_CHAT_MEMBER` 403

---

### PUT `/chats/{chat_id}` 🔒
Обновить название, описание или аватар чата. Требует роль `admin` или `owner`.

**Request:**
```json
{
  "name": "New Name",
  "description": "New description",
  "avatar_url": "https://..."
}
```
Все поля опциональны. `null` не меняет значение, поле просто не передаётся.

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_CHAT` 404, `NOT_CHAT_MEMBER` 403, `CHAT_ACCESS_DENIED` 403

---

### POST `/chats/{chat_id}/members` 🔒
Добавить пользователя в чат. Требует роль `admin` или `owner`.

**Request:**
```json
{
  "user_id": 7,
  "role_id": 5
}
```
- `role_id`: ID роли (1 — owner, 2 — admin, 5 — member, 6 — viewer)

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_CHAT` 404, `ALREADY_CHAT_MEMBER` 409, `MEMBER_LIMIT_EXCEEDED` 400, `CHAT_ACCESS_DENIED` 403

---

### DELETE `/chats/{chat_id}/members/{user_id}` 🔒
Выгнать участника из чата. Требует роль `admin` или `owner`; нельзя кикнуть пользователя с более высокой ролью.

**Response 204**

**Ошибки:** `NOT_FOUND_CHAT` 404, `NOT_CHAT_MEMBER` 403, `CHAT_ACCESS_DENIED` 403

---

### PUT `/chats/{chat_id}/members/{user_id}/role` 🔒
Изменить роль участника. Только `owner`.

**Request:**
```json
{
  "role_id": 2
}
```

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_CHAT` 404, `NOT_CHAT_MEMBER` 403, `CHAT_ACCESS_DENIED` 403

---

### POST `/chats/{chat_id}/leave` 🔒
Покинуть чат. Owner может покинуть чат только если он единственный участник.

**Response 204**

**Ошибки:** `NOT_CHAT_MEMBER` 403, `CHAT_ACCESS_DENIED` 403

---

### POST `/chats/{chat_id}/members/{user_id}/ban` 🔒
Забанить или разбанить участника. Требует роль `admin` или `owner`.

**Request:**
```json
{
  "ban": true
}
```
- `ban: true` — заблокировать; `ban: false` — разблокировать

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_CHAT` 404, `NOT_CHAT_MEMBER` 403, `CHAT_ACCESS_DENIED` 403

---

### GET `/chats/{chat_id}/presence` 🔒
Онлайн-статус всех участников чата.

**Response 200 — ChatPresenceDTO:**
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

**Ошибки:** `NOT_CHAT_MEMBER` 403

---

### GET `/chats/{chat_id}/messages` 🔒
Сообщения чата — cursor-based пагинация (от новых к старым).

**Query params:**
```
limit: integer (default 30, min 30, max 100)
before_id: integer | null — загрузить сообщения старше этого ID
```

**Response 200 — MessageCursorPage:**
```json
{
  "items": [
    {
      "id": 101,
      "chat_id": 42,
      "author_id": 1,
      "type": "text",
      "content": "Hello!",
      "reply_to_id": null,
      "media_url": null,
      "is_deleted": false,
      "is_edited": false,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "next_cursor": 95,
  "has_more": true,
  "read_cursors": {}
}
```

| Поле | Описание |
|------|----------|
| `next_cursor` | ID последнего сообщения для следующего запроса (`before_id=next_cursor`) |
| `has_more` | Есть ли ещё сообщения |
| `read_cursors` | Всегда пустой объект `{}` в этом эндпоинте; детальные курсоры доступны через `/read-details` |

**Паттерн загрузки истории:**
```
// Первая загрузка
GET /chats/42/messages?limit=30

// Подгрузка следующей страницы
GET /chats/42/messages?limit=30&before_id={next_cursor из предыдущего ответа}
```

**Ошибки:** `NOT_CHAT_MEMBER` 403

---

### GET `/chats/{chat_id}/messages/read-details` 🔒
Курсоры прочтения по каждому участнику чата. Cursor-based пагинация по `user_id`.

**Query params:**
```
limit: integer (1–200, default 50)
after_user_id: integer | null — загрузить записи с user_id строго больше указанного
```

**Response 200 — MessageReadDetailsPageDTO:**
```json
{
  "items": [
    { "user_id": 1, "last_read_message_id": 101 },
    { "user_id": 5, "last_read_message_id": 98 }
  ],
  "next_cursor": 5,
  "has_more": false
}
```

**Ошибки:** `NOT_CHAT_MEMBER` 403

---

### POST `/chats/{chat_id}/messages` 🔒
Отправить сообщение в чат.

**Request:**
```json
{
  "content": "Hello, world!",
  "reply_to_id": null,
  "message_type": "text"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `content` | `string` | Текст сообщения (max 4096 символов) |
| `reply_to_id` | `integer \| null` | ID сообщения, на которое отвечаем |
| `message_type` | `text \| image \| file \| reply` | Тип (default `text`) |

**Response 201:**
```json
{
  "message_id": 102,
  "chat_id": 42,
  "created_at": "2024-01-15T10:31:00Z"
}
```

**Ошибки:** `NOT_FOUND_CHAT` 404, `NOT_CHAT_MEMBER` 403, `CHAT_ACCESS_DENIED` 403, `MESSAGE_TOO_LONG` 400

---

### PUT `/chats/{chat_id}/messages/{message_id}` 🔒
Редактировать сообщение. Только автор сообщения.

**Request:**
```json
{
  "content": "Edited text"
}
```

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_MESSAGE` 404, `CHAT_ACCESS_DENIED` 403

---

### DELETE `/chats/{chat_id}/messages/{message_id}` 🔒
Удалить сообщение. Автор может удалить своё; `admin`/`owner` — любое.

**Response 204**

**Ошибки:** `NOT_FOUND_MESSAGE` 404, `NOT_CHAT_MEMBER` 403, `CHAT_ACCESS_DENIED` 403

---

### POST `/chats/{chat_id}/messages/read` 🔒
Отметить сообщения прочитанными вплоть до указанного ID.

**Request:**
```json
{
  "message_id": 101
}
```

**Response 204**

**Ошибки:** `NOT_CHAT_MEMBER` 403

---

### GET `/chats/{chat_id}/messages/{message_id}/delivery` 🔒
Статус доставки сообщения (доставлено ли на устройства участников).

**Response 200 — MessageDeliveryStatusDTO:**
```json
{
  "message_id": 102,
  "delivered_to": {
    "1": true,
    "5": false
  }
}
```

**Ошибки:** `NOT_CHAT_MEMBER` 403

---

## WebSocket

### Подключение

```
WS /api/v1/chats/ws/?token=<access_token>
```

Одно соединение на пользователя получает **все** события по всем его чатам.  
При невалидном токене сервер закрывает соединение с кодом `4001`.

---

### Формат всех серверных событий

```json
{
  "type": "event_type",
  "chat_id": 42,
  "payload": { ... }
}
```

---

### События от сервера к клиенту

#### `new_message`
Новое сообщение в чате.

```json
{
  "type": "new_message",
  "chat_id": 42,
  "payload": {
    "id": 103,
    "chat_id": 42,
    "author_id": 5,
    "content": "Hey!",
    "created_at": "2024-01-15T10:35:00Z",
    "is_edited": false,
    "reply_to_id": null
  }
}
```

#### `message_deleted`
Сообщение удалено.

```json
{
  "type": "message_deleted",
  "chat_id": 42,
  "payload": {
    "message_id": 101
  }
}
```

#### `message_edited`
Сообщение отредактировано.

```json
{
  "type": "message_edited",
  "chat_id": 42,
  "payload": {
    "id": 101,
    "chat_id": 42,
    "author_id": 1,
    "content": "Updated text"
  }
}
```

#### `messages_read`
Участник прочитал сообщения.

```json
{
  "type": "messages_read",
  "chat_id": 42,
  "payload": {
    "user_id": 5,
    "last_read_message_id": 103
  }
}
```

#### `member_left`
Участник покинул чат.

```json
{
  "type": "member_left",
  "chat_id": 42,
  "payload": {
    "user_id": 5
  }
}
```

#### `member_kick`
Участник выгнан из чата.

```json
{
  "type": "member_kick",
  "chat_id": 42,
  "payload": {
    "user_id": 5,
    "kicked_by": 1
  }
}
```

#### `typing_start`
Участник начал печатать.

```json
{
  "type": "typing_start",
  "chat_id": 42,
  "payload": {
    "user_id": 5,
    "ts": "2024-01-15T10:35:00Z"
  }
}
```

#### `typing_stop`
Участник перестал печатать.

```json
{
  "type": "typing_stop",
  "chat_id": 42,
  "payload": {
    "user_id": 5,
    "ts": "2024-01-15T10:35:00Z"
  }
}
```

#### `ping`
Heartbeat от сервера (каждые ~30 секунд). Отвечать не нужно.

```json
{
  "type": "ping",
  "ts": "2024-01-15T10:35:00Z"
}
```

---

### События от клиента к серверу

Клиент отправляет JSON через WebSocket-соединение:

```json
{
  "type": "event_type",
  "chat_id": 42,
  "payload": { ... }
}
```

#### Отправить индикатор набора текста
```json
{
  "type": "typing_start",
  "chat_id": 42,
  "payload": {}
}
```

#### Остановить индикатор набора текста
```json
{
  "type": "typing_stop",
  "chat_id": 42,
  "payload": {}
}
```

#### Подтвердить доставку сообщения
```json
{
  "type": "new_message",
  "chat_id": 42,
  "payload": {
    "message_id": 103
  }
}
```

---

### WS коды закрытия

| Код | Причина |
|-----|---------|
| `4001` | Невалидный или истёкший токен |
| `1008` | Слишком много соединений от пользователя (лимит: 2) |

---

### Типичная WS-логика на клиенте

```javascript
// 1. Подключение
const ws = new WebSocket(`wss://api.example.com/api/v1/chats/ws/?token=${accessToken}`);

// 2. Получение событий
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case 'new_message':
      addMessage(data.chat_id, data.payload);
      // подтвердить доставку
      ws.send(JSON.stringify({
        type: 'new_message',
        chat_id: data.chat_id,
        payload: { message_id: data.payload.id }
      }));
      break;
    case 'message_deleted':
      removeMessage(data.chat_id, data.payload.message_id);
      break;
    case 'message_edited':
      updateMessage(data.chat_id, data.payload.id, data.payload.content);
      break;
    case 'messages_read':
      updateReadCursor(data.chat_id, data.payload.user_id, data.payload.last_read_message_id);
      break;
    case 'typing_start':
      showTypingIndicator(data.chat_id, data.payload.user_id);
      break;
    case 'typing_stop':
      hideTypingIndicator(data.chat_id, data.payload.user_id);
      break;
    case 'ping':
      // ничего не делать
      break;
  }
};

// 3. Переподключение при разрыве
ws.onclose = (event) => {
  if (event.code !== 4001) {
    // переподключиться через 2 секунды
    setTimeout(connect, 2000);
  }
};
```

---

## Пагинация

Большинство эндпоинтов, возвращающих списки, поддерживают offset-пагинацию:

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

> **Исключения:** следующие эндпоинты используют cursor-based пагинацию и не поддерживают `page`/`page_size`/`sort`:
> - `GET /chats/my` — параметры `cursor` и `limit`
> - `GET /chats/{chat_id}/messages` — параметры `before_id` и `limit`
> - `GET /chats/{chat_id}/messages/read-details` — параметры `after_user_id` и `limit`

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

### ChatRoleId (роли в чате, передаются как role_id)
```
1 — owner        — создатель, все права
2 — admin        — управление участниками, редактирование чата
4 — direct       — участник direct-чата (назначается автоматически)
5 — member       — чтение и отправка сообщений
6 — viewer       — только чтение
```

**Матрица прав участников чата:**

| Действие | viewer | member | direct | admin | owner |
|----------|--------|--------|--------|-------|-------|
| Читать сообщения | ✓ | ✓ | ✓ | ✓ | ✓ |
| Отправлять сообщения | — | ✓ | ✓ | ✓ | ✓ |
| Редактировать своё сообщение | — | ✓ | ✓ | ✓ | ✓ |
| Удалять своё сообщение | — | ✓ | ✓ | ✓ | ✓ |
| Закреплять сообщения | — | — | ✓ | ✓ | ✓ |
| Удалять любое сообщение | — | — | — | ✓ | ✓ |
| Добавлять участников | — | — | — | ✓ | ✓ |
| Удалять участников | — | — | — | ✓ | ✓ |
| Банить участников | — | — | — | ✓ | ✓ |
| Редактировать чат (название/описание) | — | — | ✓ | ✓ | ✓ |
| Удалить чат | — | — | — | — | ✓ |
| Менять роли участников | — | — | — | — | ✓ |

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