# API Documentation — Full Frontend Reference
> **Версия:** синхронизирована с кодом. Предназначена для AI-генерации frontend.  
> Все типы взяты из реальных Pydantic DTO/Schema файлов.

---

## Содержание

1. [Общее](#1-общее)
2. [Типы данных (TypeScript-интерфейсы)](#2-типы-данных)
3. [Аутентификация](#3-аутентификация)
4. [Пользователи](#4-пользователи)
5. [Профили](#5-профили)
6. [Проекты](#6-проекты)
7. [Позиции](#7-позиции)
8. [Заявки](#8-заявки)
9. [Роли и права](#9-роли-и-права)
10. [Сессии](#10-сессии)
11. [Чаты](#11-чаты)
12. [Сообщения](#12-сообщения)
13. [WebSocket — события и payload](#13-websocket)
14. [Пагинация](#14-пагинация)
15. [Формат ошибок](#15-формат-ошибок)

---

## 1. Общее

### Base URL
```
/api/v1
```

### Аутентификация запросов
Все 🔒-эндпоинты требуют заголовок:
```
Authorization: Bearer <access_token>
```

### ID-типы

| Сущность    | Тип           | Пример                               |
|-------------|---------------|--------------------------------------|
| User        | `number`      | `1`                                  |
| Project     | `number`      | `42`                                 |
| Session     | `number`      | `7`                                  |
| Profile     | `number`      | `3`                                  |
| Chat        | `number`      | `100`                                |
| Message     | `number`      | `5001`                               |
| Position    | `string UUID` | `"550e8400-e29b-41d4-a716-446655440000"` |
| Application | `string UUID` | `"550e8400-e29b-41d4-a716-446655440001"` |
| Attachment  | `string UUID` | `"6d0de7a6-94b6-42ba-9005-62f40e7652f6"` |

---

## 2. Типы данных

Точные TypeScript-интерфейсы, соответствующие Pydantic DTOs.

```typescript
// ─── Auth ────────────────────────────────────────────────────────────────────

interface AccessTokenResponse {
  access_token: string;
}

// ─── Users ───────────────────────────────────────────────────────────────────

/** Возвращается из POST /users/register и GET /users/me */
interface UserResponse {
  id: number;
  username: string;   // 4–100 символов, pattern: ^[a-zA-Z0-9 ,.\'-]+$
  email: string;
}

interface PermissionDTO {
  id: number;
  name: string;       // например "read:chat", "write:message"
}

interface RoleDTO {
  id: number;
  name: string;
  description: string;
  security_level: number;
  permissions: PermissionDTO[];
}

interface SessionDTO {
  id: number;
  user_id: number;
  device_info: string;
  user_agent: string;
  last_activity: string;  // ISO 8601 datetime
  is_active: boolean;
}

/** Полный DTO пользователя — возвращается из GET /users/ */
interface UserDTO {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  roles: RoleDTO[];
  permissions: PermissionDTO[];
  sessions: SessionDTO[];
}

// ─── Profiles ────────────────────────────────────────────────────────────────

interface ContactDTO {
  profile_id: number;
  provider: string;   // например "github", "telegram"
  contact: string;    // URL или username
}

/**
 * avatars: ключ — вариант размера (число), значение — объект с URL.
 * Пример: { 128: { url: "https://..." }, 256: { url: "https://..." } }
 */
interface ProfileDTO {
  id: number;
  avatars: Record<number, Record<string, string>>;
  specialization: string | null;
  display_name: string | null;
  bio: string | null;
  date_birthday: string | null;   // "YYYY-MM-DD"
  skills: string[];               // уникальные значения (set)
  contacts: ContactDTO[];
}

interface AvatarPresignResponse {
  url: string;                    // URL для POST в S3
  fields: Record<string, string>; // поля для multipart/form-data
  key_base: string;               // нужен для upload_complete
}

// ─── Projects ─────────────────────────────────────────────────────────────────

interface ProjectRoleDTO {
  id: number;
  name: string;                   // "owner" | "admin" | "member" | "viewer"
  permissions: Record<string, unknown>;
}

interface MemberDTO {
  id: number;
  project_id: number;
  user_id: number;
  role_id: number | null;
  status: string;                 // "pending" | "active" | "rejected"
  invited_by: number | null;
  joined_at: string | null;       // ISO 8601 datetime
  permissions_overrides: Record<string, unknown>;
  role: ProjectRoleDTO | null;
  project: ProjectDTO | null;
}

interface ProjectDTO {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description: string | null;
  full_description: string | null;
  visibility: "public" | "private";
  meta_data: Record<string, unknown>;
  tags: string[];
  created_at: string | null;      // ISO 8601 datetime
  updated_at: string | null;
  memberships: MemberDTO[];
}

// ─── Positions ────────────────────────────────────────────────────────────────

interface PositionDTO {
  id: string;                     // UUID
  project_id: number;
  title: string;
  description: string;
  responsibilities: string | null;
  required_skills: string[];      // set
  is_open: boolean;
  location_type: "remote" | "onsite" | "hybrid";
  expected_load: "low" | "medium" | "high";
}

// ─── Applications ─────────────────────────────────────────────────────────────

interface ApplicationDTO {
  id: string;                     // UUID
  project_id: number;
  position_id: string;            // UUID
  candidate_id: number;
  status: "pending" | "accepted" | "rejected";
  message: string | null;
  decided_by: number | null;
  decided_at: string | null;      // ISO 8601 datetime
}

// ─── Chats ────────────────────────────────────────────────────────────────────

interface MemberInfoDTO {
  user_id: number;
  role_id: number;
  is_muted: boolean;
  is_banned: boolean;
  permissions_overrides: Record<string, boolean>;
}

interface MemberPresenceDTO {
  user_id: number;
  is_online: boolean;
}

interface ChatDTO {
  id: string; // UUID
  seq_counter: number;
  last_activity_at: string | null;
  type: "direct" | "group" | "channel";
  name: string | null;
  description: string | null;
  avatar_s3_key: string | null;
  is_public: boolean;
  admin_only: boolean;
  slow_mode_seconds: number;
  permissions: Record<string, boolean>;
  created_by: number;
  member_count: number;
  unread_count: number;
}

interface ChatDetailDTO extends Omit<ChatDTO, "unread_count"> {
  members: MemberInfoDTO[];
}

interface ListChatsDTO {
  has_next: boolean;
  chats: ChatDTO[];
  next_date: string | null;
  next_chat_id: string | null; // UUID
}

// ─── Messages ─────────────────────────────────────────────────────────────────

interface AttachmentDTO {
  id: string;                   // UUID
  message_id: string | null;    // UUID
  chat_id: string;              // UUID
  uploader_id: number;
  attachment_type: "image" | "video" | "file";
  attachment_status: string;
  url: string | null;
  url_expires_in: number | null;
  s3_key: string;
  mime_type: string;
  original_filename: string;
  size: number;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  created_at: string;
}

interface MessageDTO {
  id: string;
  chat_id: string;
  seq: number;
  author_id: number | null;
  type: string;
  content: string | null;
  reply_to_id: string | null;
  forwarded_from_chat_id: string | null;
  forwarded_from_message_id: string | null;
  forwarded_from_author_id: number | null;
  is_edited: boolean;
  created_at: string;
  reply_to: MessageDTO | null;
  forwarded_from: MessageDTO | null;
  attachments: AttachmentDTO[];
}

interface MessagesDTO {
  messages: MessageDTO[];
  next_cursor: number | null;
  has_next: boolean;
}

interface UploadSlotDTO {
  upload_token: string;
  upload_url: string;             // presigned S3 PUT URL
  attachment_type: "image" | "video" | "file";
  expires_in: number;             // секунды (обычно 300)
}

interface AttachmentDownloadUrlDTO {
  attachment_id: string;          // UUID
  url: string;                    // presigned S3 GET URL
  expires_in: number;             // секунды (300)
}

interface SendMessageResult {
  message_id: number;
  chat_id: number;
  created_at: string;             // ISO 8601 datetime
  attachment_count: number;
}

interface ForwardMessageResult {
  message_id: number;
  chat_id: number;
  created_at: string;
  attachment_count: number;
}

// ─── LiveKit / Calls ──────────────────────────────────────────────────────────

interface JoinTokenDTO {
  token: string;                  // JWT для LiveKit SDK
  slug: string;                   // формат: "chat:<chat_id>"
  livekit_url: string;            // wss://...
}

interface LiveKitParticipantsDTO {
  identity: string;               // строка user_id
  name: string;                   // username
  state: number;                  // LiveKit participant state enum
  joined_at: number;              // unix timestamp
}

// ─── Pagination ───────────────────────────────────────────────────────────────

interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
```

---

## 3. Аутентификация

### POST `/auth/login`

Логин по username/password (form-data).

**Request** `application/x-www-form-urlencoded`:
```
username: string   (обязательно)
password: string   (обязательно)
```

**Response 200 → `AccessTokenResponse`:**
```json
{ "access_token": "eyJ..." }
```
> Refresh token устанавливается в httpOnly cookie `refresh_token`.

**Ошибки:** `WRONG_LOGIN_DATA` 400

---

### POST `/auth/refresh/`

**Лимит:** 4 запроса за 5 минут.  
Берёт refresh token из cookie `refresh_token`.

**Response 200 → `AccessTokenResponse`**

> Новый refresh token обновляет cookie.

**Ошибки:** `INVALID_TOKEN` 403, `EXPIRED_TOKEN` 400, `NOT_FOUND_OR_INACTIVE_SESSION` 400

---

### POST `/auth/logout/`

Инвалидирует текущий refresh token из cookie.

**Response 204** (no content)

**Ошибки:** `INVALID_TOKEN` 400

---

### POST `/auth/verifications/email/`

**Лимит:** 3 запроса в час.

**Request `application/json`:**
```json
{ "email": "user@example.com" }
```

**Response 204** (no content)

**Ошибки:** `NOT_FOUND_USER` 404

---

### POST `/auth/verifications/email/verify/`

**Лимит:** 3 запроса в час.

**Request:**
```json
{ "token": "string" }
```

**Response 204** (no content)

**Ошибки:** `INVALID_TOKEN` 403, `NOT_FOUND_USER` 404

---

### POST `/auth/password-resets/`

**Лимит:** 3 запроса в час.

**Request:**
```json
{ "email": "user@example.com" }
```

**Response 204** (no content)

**Ошибки:** `NOT_FOUND_USER` 404

---

### POST `/auth/password-resets/confirm/`

**Лимит:** 3 запроса в час.

**Request:**
```json
{
  "token": "string",
  "password": "string",
  "password_repeat": "string"
}
```

> ⚠️ Поле называется `password_repeat`.

**Валидация пароля** (8–128 символов):
- минимум 1 заглавная буква `[A-Z]`
- минимум 1 строчная буква `[a-z]`
- минимум 1 цифра `[0-9]`
- минимум 1 спецсимвол из `!@#$%^&*(),.?":{}|<>`

**Response 204** (no content)

**Ошибки:** `INVALID_TOKEN` 403, `PASSWORD_MISMATCH` 400, `NOT_FOUND_USER` 404

---

### GET `/auth/oauth/{provider}/authorize/`

**Response 200 → `OAuthUrlResponse`:**
```json
{ "url": "https://accounts.google.com/o/oauth2/v2/auth?..." }
```

> Фронтенд должен сам выполнить редирект на полученный `url`.

**Ошибки:** `NOT_EXIST_PROVIDER_OAUTH` 400

---

### GET `/auth/oauth/{provider}/authorize/connect/` 🔒

Привязать OAuth к существующему аккаунту.

**Response 200 → `OAuthUrlResponse`:**
```json
{ "url": "https://accounts.google.com/o/oauth2/v2/auth?..." }
```

> Фронтенд должен сам выполнить редирект на полученный `url`.

**Ошибки:** `NOT_EXIST_PROVIDER_OAUTH` 400

---

### GET `/auth/oauth/{provider}/callback/`

**Query params:**
```
code:  string  (обязательно)
state: string  (обязательно)
```

**Response 200 → `AccessTokenResponse`**

> Refresh token устанавливается в cookie.

**Ошибки:** `NOT_EXIST_PROVIDER_OAUTH` 400, `OAUTH_STATE_NOT_FOUND` 404, `NOT_FOUND_USER` 404, `LINKED_ANOTHER_USER_OAUTH` 409

---

## 4. Пользователи

### POST `/users/register/`

**Request:**
```json
{
  "username": "johndoe",
  "email": "user@example.com",
  "password": "Secret1!",
  "password_repeat": "Secret1!"
}
```

| Поле              | Тип    | Валидация                                        |
|-------------------|--------|--------------------------------------------------|
| `username`        | string | 4–100 символов, pattern: `^[a-zA-Z0-9 ,.\'-]+$` |
| `email`           | string | валидный email                                   |
| `password`        | string | 8–128 символов, см. валидацию выше               |
| `password_repeat` | string | должен совпадать с `password`                    |

**Response 201 → `UserResponse`:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "user@example.com"
}
```

**Ошибки:** `DUPLICATE_USER` 409, `PASSWORD_MISMATCH` 400, `VALIDATION_EXCEPTION` 422

---

### GET `/users/me/` 🔒

**Response 200 → `UserResponse`** (только `id`, `username`, `email`):
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "user@example.com"
}
```

**Ошибки:** `INVALID_TOKEN` 400, `ACCESS_DENIED` 403, `NOT_FOUND_USER` 404

---

### GET `/users/` 🔒

**Query params:**
```
email:              string   — частичное совпадение
username:           string   — частичное совпадение
is_active:          boolean
is_verified:        boolean
is_deleted:         boolean
created_after:      datetime — ISO 8601
created_before:     datetime
updated_after:      datetime
updated_before:     datetime
has_oauth_accounts: boolean
has_sessions:       boolean
role_names:         string[] — повторяющийся: ?role_names=admin&role_names=member
permission_names:   string[] — повторяющийся
page:               number   (default: 1, min: 1)
page_size:          number   (default: 20, min: 1, max: 100)
sort:               string   (default: created_at:desc)
```

**Response 200 → `PageResult<UserDTO>`:**
```json
{
  "items": [
    {
      "id": 1,
      "username": "johndoe",
      "email": "user@example.com",
      "is_active": true,
      "is_verified": true,
      "roles": [
        {
          "id": 1,
          "name": "member",
          "description": "Regular member",
          "security_level": 1,
          "permissions": [{ "id": 5, "name": "read:profile" }]
        }
      ],
      "permissions": [{ "id": 5, "name": "read:profile" }],
      "sessions": [
        {
          "id": 3,
          "user_id": 1,
          "device_info": "Chrome on Windows",
          "user_agent": "Mozilla/5.0...",
          "last_activity": "2026-03-31T10:00:00Z",
          "is_active": true
        }
      ]
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### GET `/users/sessions/` 🔒

**Response 200 → `SessionDTO[]`:**
```json
[
  {
    "id": 3,
    "user_id": 1,
    "device_info": "Chrome on Windows",
    "user_agent": "Mozilla/5.0...",
    "last_activity": "2026-03-31T10:00:00Z",
    "is_active": true
  }
]
```

---

### POST `/users/{user_id}/roles/` 🔒

**Request:**
```json
{ "role_name": "admin" }
```

**Response 200:** `{}`

**Ошибки:** `INVALID_TOKEN` 400, `ACCESS_DENIED` 403, `NOT_FOUND_USER` 404, `NOT_FOUND_ROLE` 404

---

### DELETE `/users/{user_id}/roles/{role_name}/` 🔒

**Response 204** (no content)

**Ошибки:** `INVALID_TOKEN` 400, `ACCESS_DENIED` 403, `NOT_FOUND_USER` 404, `NOT_FOUND_ROLE` 404

---

### POST `/users/{user_id}/permissions/` 🔒

**Request:**
```json
{ "permissions": ["read:chat", "write:message"] }
```

**Response 200:** `{}`

---

### DELETE `/users/{user_id}/permissions/` 🔒

**Request:**
```json
{ "permissions": ["read:chat"] }
```

**Response 204** (no content)

---

## 5. Профили

### POST `/profiles/` 🔒

**Request:**
```json
{
  "display_name": "John Doe",
  "bio": "Backend developer",
  "skills": ["Python", "FastAPI"],
  "date_birthday": "1990-01-15"
}
```

| Поле           | Тип           | Обязательность |
|----------------|---------------|----------------|
| `display_name` | string \| null | нет           |
| `bio`          | string \| null | нет           |
| `skills`       | string[]       | нет           |
| `date_birthday`| string (date)  | нет           |

**Response 201:** `{}`

---

### GET `/profiles/`

**Query params:**
```
username:     string   — частичное совпадение
display_name: string   — частичное совпадение
skills:       string[] — повторяющийся параметр
page:         number   (default: 1)
page_size:    number   (default: 20, max: 100)
sort:         string
```

**Response 200 → `PageResult<ProfileDTO>`:**
```json
{
  "items": [
    {
      "id": 1,
      "avatars": {
        "128": { "url": "https://cdn.example.com/avatars/user_1_128.jpg" },
        "256": { "url": "https://cdn.example.com/avatars/user_1_256.jpg" }
      },
      "specialization": "Backend Engineer",
      "display_name": "John Doe",
      "bio": "Loves Python",
      "date_birthday": "1990-01-15",
      "skills": ["Python", "FastAPI"],
      "contacts": [
        { "profile_id": 1, "provider": "github", "contact": "https://github.com/johndoe" }
      ]
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### GET `/profiles/{profile_id}/`

**Response 200 → `ProfileDTO`**

**Ошибки:** `NOT_FOUND_PROFILE` 404

---

### PUT `/profiles/{profile_id}/` 🔒

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

> Все поля опциональны. `null` не сбрасывает значение — просто не передавайте поле.

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_PROFILE` 404, `ACCESS_DENIED` 403

---

### POST `/profiles/avatar/presign/` 🔒

**Лимит:** 4 запроса за 5 минут.

**Request:**
```json
{
  "filename": "avatar.jpg",
  "content_type": "image/jpeg",
  "size": 102400
}
```

> ⚠️ `content_type` должен начинаться с `"image/"`, иначе ошибка валидации.

**Response 200 → `AvatarPresignResponse`:**
```json
{
  "url": "https://storage.example.com/bucket",
  "fields": {
    "key": "avatars/user_1/avatar",
    "Content-Type": "image/jpeg",
    "policy": "...",
    "x-amz-signature": "..."
  },
  "key_base": "avatars/user_1/avatar"
}
```

**Загрузка файла (после получения presign):**
```
POST {url}
Content-Type: multipart/form-data

fields.key=...
fields.Content-Type=...
fields.policy=...
fields.x-amz-signature=...
file=<binary>
```

---

### POST `/profiles/avatar/upload_complete/` 🔒

**Лимит:** 4 запроса за 5 минут.

**Request:**
```json
{
  "key_base": "avatars/user_1/avatar",
  "size": 102400,
  "content_type": "image/jpeg"
}
```

> `key_base` берётся из ответа `/avatar/presign`.

**Response 200:** `"OK"`

---

### POST `/profiles/{profile_id}/contacts/` 🔒

**Request:**
```json
{
  "provider": "github",
  "contact": "https://github.com/username"
}
```

**Response 200:** `{}`

---

### DELETE `/profiles/{profile_id}/{provide_contact}/delete/` 🔒

**Path param:** `provide_contact` — имя провайдера (`github`, `telegram`, …)

**Response 200:** `{}`

---

## 6. Проекты

### POST `/projects/` 🔒

**Request:**
```json
{
  "name": "My Project",
  "slug": "my-project",
  "small_description": "Short description",
  "description": "Full markdown description",
  "visibility": "public",
  "tags": ["python", "web"],
  "meta_data": {}
}
```

| Поле                | Тип            | Обязательность |
|---------------------|----------------|----------------|
| `name`              | string         | да             |
| `slug`              | string         | да             |
| `small_description` | string \| null | нет            |
| `description`       | string \| null | нет            |
| `visibility`        | `"public" \| "private"` | нет |
| `tags`              | string[]       | нет            |
| `meta_data`         | object         | нет            |

**Response 201:** `{}`

---

### GET `/projects/` 🔒

**Query params:**
```
name:      string
slug:      string
tags:      string[] — повторяющийся
page:      number (default: 1)
page_size: number (default: 20, max: 100)
sort:      string
```

**Response 200 → `PageResult<ProjectDTO>`:**
```json
{
  "items": [
    {
      "id": 1,
      "owner_id": 1,
      "name": "My Project",
      "slug": "my-project",
      "small_description": "Short description",
      "full_description": "Full markdown",
      "visibility": "public",
      "meta_data": {},
      "tags": ["python", "web"],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "memberships": []
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### GET `/projects/my/` 🔒

Проекты, в которых текущий пользователь участник.

**Query params:**
```
page:      number (default: 1)
page_size: number (default: 20, max: 100)
```

**Response 200 → `PageResult<ProjectDTO>`**

---

### GET `/projects/{project_id}/` 🔒

**Response 200 → `ProjectDTO`**

**Ошибки:** `NOT_FOUND_PROJECT` 404

---

### PUT `/projects/{project_id}/` 🔒

**Request:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "visibility": "private",
  "tags": ["python"],
  "meta_data": {}
}
```

> Все поля опциональны.

**Response 200:** `{}`

**Ошибки:** `NOT_FOUND_PROJECT` 404, `ACCESS_DENIED` 403

---

### DELETE `/projects/{project_id}/` 🔒

**Response 204** (no content)

**Ошибки:** `NOT_FOUND_PROJECT` 404, `ACCESS_DENIED` 403

---

### GET `/projects/{project_id}/positions/`

**Query params:**
```
title:           string
required_skills: string[]
is_open:         boolean (default: true)
location_type:   "remote" | "onsite" | "hybrid" (default: "remote")
expected_load:   "low" | "medium" | "high" (default: "low")
page:            number (default: 1)
page_size:       number (default: 20)
sort:            string
```

**Response 200 → `PageResult<PositionDTO>`**

---

### POST `/projects/{project_id}/positions/` 🔒

**Request:**
```json
{
  "title": "Backend Developer",
  "description": "We need a Python dev",
  "responsibilities": "Build APIs",
  "required_skills": ["Python", "PostgreSQL"],
  "location_type": "remote",
  "expected_load": "high"
}
```

| Поле               | Тип       | Обязательность |
|--------------------|-----------|----------------|
| `title`            | string    | да             |
| `description`      | string    | да             |
| `responsibilities` | string    | нет            |
| `required_skills`  | string[]  | нет            |
| `location_type`    | string    | нет            |
| `expected_load`    | string    | нет            |

**Response 201:** `{}`

---

### POST `/projects/{project_id}/invite/` 🔒

**Request:**
```json
{
  "user_id": 5,
  "role_id": 2,
  "permissions_overrides": { "write:positions": true }
}
```

> `permissions_overrides` — произвольный объект (словарь прав), опционально.

**Response 200:** `{}`

---

### POST `/projects/{project_id}/members/accept/` 🔒

Принять приглашение (текущий пользователь).

**Response 200:** `{}`

---

### PUT `/projects/{project_id}/members/{user_id}/permissions/` 🔒

**Request:**
```json
{
  "permissions_overrides": { "write:positions": true, "read:applications": true }
}
```

**Response 200:** `{}`

---

### GET `/projects/invites/my/` 🔒

Приглашения в проекты для текущего пользователя.

**Response 200 → `PageResult<MemberDTO>`:**
```json
{
  "items": [
    {
      "id": 1,
      "project_id": 42,
      "user_id": 1,
      "role_id": 3,
      "status": "pending",
      "invited_by": 5,
      "joined_at": null,
      "permissions_overrides": {},
      "role": {
        "id": 3,
        "name": "member",
        "permissions": {}
      },
      "project": null
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

---

## 7. Позиции

### GET `/positions/`

**Query params:**
```
project_id:      number
title:           string   — частичное совпадение
required_skills: string[] — повторяющийся
is_open:         boolean  (default: true)
location_type:   "remote" | "onsite" | "hybrid" (default: "remote")
expected_load:   "low" | "medium" | "high" (default: "low")
page:            number (default: 1)
page_size:       number (default: 20, max: 100)
sort:            string
```

**Response 200 → `PageResult<PositionDTO>`:**
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

### GET `/positions/{position_id}/`

**Response 200 → `PositionDTO`**

---

### PUT `/positions/{position_id}/` 🔒

**Request:**
```json
{
  "title": "Senior Backend Developer",
  "description": "Updated description",
  "responsibilities": "Updated responsibilities",
  "required_skills": ["Python", "PostgreSQL", "Redis"],
  "location_type": "hybrid",
  "expected_load": "medium"
}
```

> Все поля опциональны.

**Response 200:** `{}`

---

### DELETE `/positions/{position_id}/` 🔒

**Response 204** (no content)

---

### GET `/positions/{position_id}/applications/`

**Query params:**
```
project_id:   number
candidate_id: number
status:       "pending" | "accepted" | "rejected" (default: "pending")
page:         number (default: 1)
page_size:    number (default: 20, max: 100)
sort:         string
```

**Response 200 → `PageResult<ApplicationDTO>`**

---

### POST `/positions/{position_id}/applications/` 🔒

**Request:**
```json
{ "message": "I'd like to join because..." }
```

> Поле `message` опционально (может быть `null`).

**Response 201:** `{}`

---

## 8. Заявки

### GET `/applications/`

**Query params:**
```
project_id:   number
position_id:  string (UUID)
candidate_id: number
status:       "pending" | "accepted" | "rejected" (default: "pending")
page:         number (default: 1)
page_size:    number (default: 20, max: 100)
sort:         string
```

**Response 200 → `PageResult<ApplicationDTO>`:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "project_id": 1,
      "position_id": "550e8400-e29b-41d4-a716-446655440000",
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

### GET `/applications/me/` 🔒

**Query params:**
```
position_id: string (UUID)
project_id:  number
status:      "pending" | "accepted" | "rejected" (default: "pending")
page:        number (default: 1)
page_size:   number (default: 20, max: 100)
sort:        string
```

**Response 200 → `PageResult<ApplicationDTO>`**

---

### POST `/applications/{application_id}/approve/` 🔒

**Response 200:** `{}`

---

### POST `/applications/{application_id}/reject/` 🔒

**Response 200:** `{}`

---

## 9. Роли и права

### POST `/roles/` 🔒

**Request:**
```json
{
  "name": "moderator",
  "description": "Can moderate content",
  "security_level": 2,
  "permissions": ["read:chat", "delete:message"]
}
```

| Поле             | Тип      | Обязательность |
|------------------|----------|----------------|
| `name`           | string   | да             |
| `description`    | string   | да             |
| `security_level` | number   | да             |
| `permissions`    | string[] | нет (set)      |

**Response 201:** `{}`

**Ошибки:** `DUPLICATE_ROLE` 409, `INVALID_ROLE_NAME` 400, `ACCESS_DENIED` 403, `NOT_FOUND_PERMISSIONS` 404

---

### GET `/roles/` 🔒

**Query params:**
```
name:               string
security_level:     number  — точное совпадение
min_security_level: number
max_security_level: number
permission_names:   string[] — повторяющийся
page:               number (default: 1)
page_size:          number (default: 20, max: 100)
sort:               string
```

**Response 200 → `PageResult<RoleDTO>`:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "admin",
      "description": "Administrator",
      "security_level": 5,
      "permissions": [
        { "id": 1, "name": "read:all" },
        { "id": 2, "name": "write:all" }
      ]
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20
}
```

---

### POST `/roles/{role_name}/permissions/` 🔒

**Request:**
```json
{ "permission": ["delete:message"] }
```

> ⚠️ Поле называется `permission` (тип `set[str]`).

**Response 200:** `{}`

---

### DELETE `/roles/{role_name}/permissions/` 🔒

**Request:**
```json
{ "permission": ["delete:message"] }
```

**Response 200:** `{}`

---

### GET `/project_roles/`

**Query params:**
```
name:      string
page:      number (default: 1)
page_size: number (default: 20, max: 100)
sort:      string
```

**Response 200 → `PageResult<ProjectRoleDTO>`:**
```json
{
  "items": [
    { "id": 1, "name": "owner", "permissions": {} },
    { "id": 2, "name": "admin", "permissions": {} },
    { "id": 3, "name": "member", "permissions": {} },
    { "id": 4, "name": "viewer", "permissions": {} }
  ],
  "total": 4,
  "page": 1,
  "page_size": 20
}
```

---

### POST `/permissions/` 🔒

**Request:**
```json
{ "name": "delete:message" }
```

**Response 201:** `{}`

---

### GET `/permissions/` 🔒

**Query params:**
```
name:      string
page:      number (default: 1)
page_size: number (default: 20, max: 100)
sort:      string
```

**Response 200 → `PageResult<PermissionDTO>`:**
```json
{
  "items": [
    { "id": 1, "name": "read:chat" },
    { "id": 2, "name": "write:message" }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### DELETE `/permissions/{name}/` 🔒

**Response 204** (no content)

**Ошибки:** `ACCESS_DENIED` 403, `PROTECTED_PERMISSION` 409

---

## 10. Сессии

### GET `/sessions/` 🔒

**Query params:**
```
user_id:               number
device_id:             string
last_activity_after:   datetime (ISO 8601)
last_activity_before:  datetime (ISO 8601)
is_active:             boolean
page:                  number (default: 1)
page_size:             number (default: 20, max: 100)
sort:                  string
```

**Response 200 → `PageResult<SessionDTO>`:**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "device_info": "Chrome on Windows",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "last_activity": "2026-03-31T10:00:00Z",
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### DELETE `/sessions/{session_id}/` 🔒

**Response 204** (no content)

**Ошибки:** `ACCESS_DENIED` 403, `NOT_FOUND_OR_INACTIVE_SESSION` 400

---

## 11. Чаты

Базовый префикс: `/api/v1/chats/`

### GET `/chats` 🔒

**Query params:**
- `limit`: `number` (default `50`, min `1`, max `100`)
- `last_chat_id`: `string | null` (UUID)
- `last_activity_at`: `string | null` (ISO datetime)

**Response 200 → `ListChats`:**
```json
{
  "has_next": true,
  "next_date": "2026-03-31T10:00:00Z",
  "next_chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "chats": []
}
```

### POST `/chats/` 🔒

**Request (`CreateChatRequest`):**
```json
{
  "name": "Team Chat",
  "description": "Our team",
  "chat_type": "group",
  "member_ids": [5, 6],
  "is_public": false,
  "admin_only": false,
  "slow_mode_seconds": 0,
  "permissions": {}
}
```

**Response 201 → `ChatDTO`**

### GET `/chats/{chat_id}/` 🔒

**Response 200 → `ChatDetaiDTO`**

### PATCH `/chats/{chat_id}/` 🔒

**Request (`UpdateChatRequest`):**
```json
{
  "name": "New name",
  "description": "New description",
  "is_public": true,
  "admin_only": true,
  "slow_mode_seconds": 10,
  "permissions": {"message:send": true}
}
```

**Response 200 → `ChatDTO`**

### DELETE `/chats/{chat_id}/` 🔒

**Response 204** (no content)

### POST `/chats/{chat_id}/join/` 🔒

**Response 204** (no content)

### POST `/chats/{chat_id}/leave/` 🔒

**Response 204** (no content)

### GET `/chats/{chat_id}/members/` 🔒

**Query params:**
- `limit`: `number` (default `100`, min `1`, max `500`)
- `cursor_user_id`: `number | null`
- `include_presence`: `boolean` (default `false`)

**Response 200 → `ListMembers`**

### POST `/chats/{chat_id}/members/` 🔒

**Request (`AddMemberRequest`):**
```json
{ "user_id": 7, "role_id": 5 }
```

**Response 204** (no content)

### PATCH `/chats/{chat_id}/members/{user_id}/role/` 🔒

**Request (`ChangeMemberRoleRequest`):**
```json
{ "role_id": 2 }
```

**Response 204** (no content)

### PATCH `/chats/{chat_id}/members/{user_id}/ban/` 🔒

**Request (`BanMemberRequest`):**
```json
{ "ban": true }
```

**Response 204** (no content)

### DELETE `/chats/{chat_id}/members/{user_id}/` 🔒

**Response 204** (no content)

### POST `/chats/{chat_id}/calls/join/` 🔒

**Response 200 → `JoinTokenDTO`:**
```json
{
  "token": "eyJ...",
  "slug": "chat:550e8400-e29b-41d4-a716-446655440000",
  "livekit_url": "wss://livekit.example.com"
}
```

### POST `/chats/{chat_id}/calls/participants/{user_id}/mute/` 🔒

**Request (`MuteParticipantRequest`):**
```json
{ "muted": true }
```

**Response 204** (no content)

### POST `/chats/realtime/presence/` 🔒

**Request (`PresenceBatchRequest`):**
```json
{ "user_ids": [1, 5, 7] }
```

**Response 200 → `MemberPresenceDTO[]`**

### GET `/chats/realtime/ws/status/` 🔒

**Response 200:**
```json
{
  "gateway_id": "gw-1",
  "stream_key": "chat:events",
  "connections": 10,
  "users": 8,
  "subscribed_chats": 15
}
```

---

## 12. Сообщения и вложения

Базовый префикс: `/api/v1/chats/{chat_id}/messages`

### GET `/chats/{chat_id}/messages/` 🔒

**Query params:**
- `limit`: `number` (default `30`, min `1`, max `100`)
- `cursor_message_seq`: `number | null` (>= `0`)

**Response 200 → `MessagesDTO`**

### GET `/chats/{chat_id}/messages/context/` 🔒

**Query params:**
- `target_seq`: `number` (>= `0`)
- `limit`: `number` (default `40`, min `1`, max `100`)

**Response 200 → `MessagesDTO`**

### POST `/chats/{chat_id}/messages/` 🔒

Поддерживает заголовок `Idempotency-Key`.

**Request (`SendMessageRequest`):**
```json
{
  "content": "Hello",
  "reply_to_id": null,
  "message_type": "text",
  "upload_tokens": []
}
```

**Response 201 → `MessageDTO`**

### GET `/chats/{chat_id}/messages/{message_id}/` 🔒

**Response 200 → `MessageDTO`**

### PATCH `/chats/{chat_id}/messages/{message_id}/` 🔒

**Request (`EditMessageRequest`):**
```json
{ "content": "Edited text" }
```

**Response 200 → `MessageDTO`**

### DELETE `/chats/{chat_id}/messages/{message_id}/` 🔒

**Response 204** (no content)

### POST `/chats/{chat_id}/messages/forward/` 🔒

**Request (`ForwardMessageRequest`):**
```json
{
  "source_chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_message_id": "550e8400-e29b-41d4-a716-446655440001",
  "comment": "FYI"
}
```

**Response 201 → `MessageDTO`**

### POST `/chats/{chat_id}/messages/read/` 🔒

**Request (`MarkReadRequest`):**
```json
{ "message_seq": 120 }
```

**Response 204** (no content)

### POST `/chats/{chat_id}/attachments/upload-requests/` 🔒

**Request (`RequestAttachmentUploadRequest`):**
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

**Response 201 → `UploadSlotDTO[]`**

### POST `/chats/{chat_id}/attachments/upload-requests/confirm/` 🔒

**Request (`ConfirmAttachmentUploadRequest`):**
```json
{
  "upload_tokens": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**Response 202** (no content)

### GET `/chats/{chat_id}/messages/{message_id}/attachments/{attachment_id}/download-url/` 🔒

**Response 200 → `AttachmentDownloadUrlDTO`**

---

## 13. WebSocket

### Подключение

```
WS /api/v1/chats/ws/?token=<access_token>
```

Поддерживается subprotocol `chat.v1`.

### Событие после подключения

Сервер отправляет `ws.ready`:
```json
{
  "type": "ws.ready",
  "payload": {
    "connection_id": "...",
    "gateway_id": "...",
    "heartbeat_interval": 30,
    "heartbeat_timeout": 90,
    "reconnect": { "mode": "last_seq_per_chat", "op": "resume" }
  }
}
```

### Команды клиента

Формат (`WSClientCommand`):
```json
{ "op": "subscribe", "chat_id": "<chat_uuid>", "last_seq": 10 }
```

Поддерживаемые `op`:
- `ping`
- `pong`
- `subscribe` (нужен `chat_id`)
- `unsubscribe` (нужен `chat_id`)
- `resume` (`cursors`: объект `{ "<chat_id>": <last_seq> }`)

### Ошибки WS

При невалидной команде/кадре сервер отправляет событие:
```json
{ "type": "ws.error", "code": "BAD_COMMAND", "detail": "..." }
```
или
```json
{ "type": "ws.error", "code": "BAD_FRAME", "detail": "..." }
```

## 14. Пагинация

### Offset-пагинация

**Query params:**
```
page:      number (default: 1, min: 1)
page_size: number (default: 20, min: 1, max: 100)
sort:      string — "field:asc|desc[,field2:asc|desc]"
           пример: "created_at:desc,username:asc"
```

**Response:**
```typescript
interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
```

### Cursor-пагинация

| Эндпоинт                                          | Параметры                   | Тип cursor           |
|---------------------------------------------------|-----------------------------|----------------------|
| `GET /chats/my/`                                  | `limit`, `cursor`           | `string` (base64)    |
| `GET /chats/{id}/messages/`                       | `limit`, `before_id`        | `number` (message ID)|
| `GET /chats/{id}/messages/read-details/`          | `limit`, `after_user_id`    | `number` (user ID)   |

---

## 15. Формат ошибок

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    detail: Record<string, unknown> | unknown[] | null;
  };
  status: number;
  request_id: string;   // UUID
  timestamp: number;    // unix timestamp float
}
```

**Пример:**
```json
{
  "error": {
    "code": "NOT_FOUND_USER",
    "message": "User not found",
    "detail": { "user_id": 42 }
  },
  "status": 404,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1743400000.123
}
```

### Полный список кодов ошибок

| Code                            | HTTP  | Когда возникает                                            |
|---------------------------------|-------|------------------------------------------------------------|
| `WRONG_LOGIN_DATA`              | 400   | Неверный логин или пароль                                  |
| `INVALID_TOKEN`                 | 403   | Токен невалиден                                            |
| `EXPIRED_TOKEN`                 | 400   | Токен истёк                                                |
| `PASSWORD_MISMATCH`             | 400   | `password` и `password_repeat` не совпадают                |
| `DUPLICATE_USER`                | 409   | Email/username уже занят                                   |
| `DUPLICATE_ROLE`                | 409   | Роль с таким именем уже существует                         |
| `NOT_FOUND_USER`                | 404   | Пользователь не найден                                     |
| `NOT_FOUND_ROLE`                | 404   | Роль не найдена                                            |
| `NOT_FOUND_PERMISSIONS`         | 404   | Один или несколько permissions не найдены                  |
| `NOT_FOUND_PROFILE`             | 404   | Профиль не найден                                          |
| `NOT_FOUND_PROJECT`             | 404   | Проект не найден                                           |
| `NOT_FOUND_OR_INACTIVE_SESSION` | 400   | Сессия не найдена или завершена                            |
| `NOT_FOUND_CHAT`                | 404   | Чат не найден                                              |
| `NOT_FOUND_MESSAGE`             | 404   | Сообщение не найдено                                       |
| `NOT_CHAT_MEMBER`               | 403   | Пользователь не участник чата                              |
| `CHAT_ACCESS_DENIED`            | 403   | Недостаточно прав в чате                                   |
| `ALREADY_CHAT_MEMBER`           | 409   | Пользователь уже в чате                                    |
| `DIRECT_CHAT_EXISTS`            | 409   | Direct-чат с этим пользователем уже есть                   |
| `MEMBER_LIMIT_EXCEEDED`         | 400   | Лимит участников чата (100)                                |
| `MESSAGE_TOO_LONG`              | 400   | Сообщение > 4096 символов                                  |
| `ACCESS_DENIED`                 | 403   | Нет системных прав (`detail: { need_permissions: [...] }`) |
| `PROTECTED_PERMISSION`          | 409   | Permission защищён от изменения/удаления                   |
| `LINKED_ANOTHER_USER_OAUTH`     | 409   | OAuth уже привязан к другому пользователю                  |
| `OAUTH_STATE_NOT_FOUND`         | 404   | OAuth state устарел                                        |
| `NOT_EXIST_PROVIDER_OAUTH`      | 400   | Провайдер OAuth не поддерживается                          |
| `INVALID_ROLE_NAME`             | 400   | Недопустимые символы в имени роли                          |
| `VALIDATION_EXCEPTION`          | 422   | Ошибка валидации входных данных                            |
| `INTERNAL_EXCEPTION`            | 500   | Внутренняя ошибка сервера                                  |

### `VALIDATION_EXCEPTION` — структура detail

```json
{
  "error": {
    "code": "VALIDATION",
    "message": "Validation exception",
    "detail": [
      {
        "loc": ["body", "email"],
        "msg": "value is not a valid email address",
        "type": "value_error.email"
      }
    ]
  },
  "status": 422
}
```

### Стратегия обработки на frontend

```typescript
async function apiRequest(config: RequestConfig) {
  const res = await fetch(config);

  if (res.status === 401 || res.status === 403) {
    const refreshed = await tryRefreshToken(); // POST /auth/refresh
    if (refreshed) return apiRequest(config);  // повторить 1 раз
    else redirectToLogin();
  }

  if (res.status === 422) {
    const err: ErrorResponse = await res.json();
    // err.error.detail — массив [{loc, msg, type}]
    showFieldErrors(err.error.detail as ValidationError[]);
    return;
  }

  if (!res.ok) {
    const err: ErrorResponse = await res.json();
    logToSentry({ request_id: err.request_id, code: err.error.code });
    showErrorToast(err.error.message);
    return;
  }

  return res.json();
}
```

---

## Приложение A: Матрица прав чата

| Действие                      | viewer | member | admin | owner |
|-------------------------------|:------:|:------:|:-----:|:-----:|
| Читать сообщения              | ✓      | ✓      | ✓     | ✓     |
| Отправлять сообщения          | —      | ✓      | ✓     | ✓     |
| Редактировать своё сообщение  | —      | ✓      | ✓     | ✓     |
| Удалять своё сообщение        | —      | ✓      | ✓     | ✓     |
| Удалять чужое сообщение       | —      | —      | ✓     | ✓     |
| Добавлять участников          | —      | —      | ✓     | ✓     |
| Кикать участников             | —      | —      | ✓     | ✓     |
| Банить участников             | —      | —      | ✓     | ✓     |
| Заглушать в звонке            | —      | —      | ✓     | ✓     |
| Редактировать чат             | —      | —      | ✓     | ✓     |
| Удалить чат                   | —      | —      | —     | ✓     |
| Менять роли участников        | —      | —      | —     | ✓     |
