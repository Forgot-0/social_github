# API Documentation (Frontend Reference)

## Base URL
```
/api/v1
```

## Auth

### Tokens
- **Access token** — передаётся в заголовке: `Authorization: Bearer <token>`
- **Refresh token** — хранится в cookie `refresh_token`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Логин (form-data: `username`, `password`) → `{ access_token }` |
| POST | `/auth/refresh` | Обновить access token (берёт refresh из cookie) |
| POST | `/auth/logout` | Выход (инвалидирует refresh token) |
| POST | `/auth/verifications/email` | Отправить код верификации email (лимит 3/час) |
| POST | `/auth/verifications/email/verify` | Подтвердить email по токену `{ token }` |
| POST | `/auth/password-resets` | Отправить код сброса пароля (лимит 3/час) |
| POST | `/auth/password-resets/confirm` | Сбросить пароль `{ password, password_repeat, token }` |
| GET | `/auth/oauth/{provider}/authorize` | Получить URL для OAuth (редирект 307) |
| GET | `/auth/oauth/{provider}/authorize/connect` | Привязать OAuth к существующему юзеру 🔒 |
| GET | `/auth/oauth/{provider}/callback` | OAuth callback → `{ access_token }` |

---

## Users

| Method | Path | Description |
|--------|------|-------------|
| POST | `/users/register` | Регистрация `{ username, email, password, password_repeat }` → `UserResponse` |
| GET | `/users/me` | Текущий юзер 🔒 → `UserResponse` |
| GET | `/users/` | Список юзеров 🔒 (фильтры: email, username, is_active, is_verified, role_names, ...) |
| GET | `/users/sessions` | Активные сессии текущего юзера 🔒 |
| POST | `/users/{user_id}/roles` | Назначить роль юзеру 🔒 `{ role_name }` |
| DELETE | `/users/{user_id}/roles/{role_name}` | Снять роль 🔒 |
| POST | `/users/{user_id}/permissions` | Добавить permissions юзеру 🔒 `{ permissions: [str] }` |
| DELETE | `/users/{user_id}/permissions` | Удалить permissions 🔒 |

**UserResponse:** `{ id, username, email }`  
**UserDTO:** `{ id, username, email, is_active, is_verified, roles[], permissions[], sessions[] }`

---

## Profiles

| Method | Path | Description |
|--------|------|-------------|
| POST | `/profiles/` | Создать профиль 🔒 `{ display_name, bio, skills[], date_birthday }` |
| GET | `/profiles/` | Список профилей (фильтры: display_name, skills[]) |
| GET | `/profiles/{id}` | Один профиль → `ProfileDTO` |
| PUT | `/profiles/{id}` | Обновить профиль 🔒 `{ specialization, display_name, bio, skills[], date_birthday }` |
| POST | `/profiles/avatar/presign` | Получить presigned URL для загрузки аватара 🔒 |
| POST | `/profiles/avatar/upload_complete` | Подтвердить загрузку аватара 🔒 |
| POST | `/profiles/{id}/contacts` | Добавить контакт 🔒 `{ provider, contact }` |
| DELETE | `/profiles/{id}/{provide_contact}/delete` | Удалить контакт 🔒 |

**ProfileDTO:** `{ id, avatars{}, specialization, display_name, bio, date_birthday, skills[], contacts[] }`

---

## Projects

| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects/` | Создать проект 🔒 `{ name, slug, small_description, description, visibility, tags[], meta_data }` |
| GET | `/projects/` | Список проектов 🔒 (фильтры: name, slug, tags[]) |
| GET | `/projects/my` | Мои проекты 🔒 |
| GET | `/projects/{id}` | Один проект → `ProjectDTO` |
| PUT | `/projects/{id}` | Обновить проект 🔒 |
| DELETE | `/projects/{id}` | Удалить (если owner или admin) 🔒 |
| GET | `/projects/{id}/positions` | Позиции проекта |
| POST | `/projects/{id}/positions` | Создать позицию 🔒 |
| POST | `/projects/{id}/invite` | Пригласить участника 🔒 `{ user_id, role_id, permissions_overrides }` |
| POST | `/projects/{id}/members/accept` | Принять приглашение 🔒 |
| PUT | `/projects/{id}/members/{user_id}/permissions` | Обновить права участника 🔒 |

**ProjectDTO:** `{ id, owner_id, name, slug, small_description, full_description, visibility, tags[], meta_data{}, created_at, updated_at, memberships[] }`

---

## Positions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/positions/` | Список позиций (фильтры: project_id, title, required_skills[], is_open, location_type, expected_load) |
| GET | `/positions/{uuid}` | Одна позиция → `PositionDTO` |
| PUT | `/positions/{uuid}` | Обновить 🔒 |
| DELETE | `/positions/{uuid}` | Удалить 🔒 |
| GET | `/positions/{uuid}/applications` | Заявки на позицию |
| POST | `/positions/{uuid}/applications` | Подать заявку 🔒 `{ message? }` |

**PositionDTO:** `{ id(uuid), project_id, title, description, responsibilities, required_skills[], is_open, location_type, expected_load }`  
**location_type:** `remote | onsite | hybrid`  
**expected_load:** `low | medium | high`

---

## Applications

| Method | Path | Description |
|--------|------|-------------|
| GET | `/applications/` | Все заявки (фильтры: project_id, position_id, candidate_id, status) |
| GET | `/applications/me` | Мои заявки 🔒 |
| POST | `/applications/{uuid}/approve` | Одобрить 🔒 |
| POST | `/applications/{uuid}/reject` | Отклонить 🔒 |

**ApplicationDTO:** `{ id(uuid), project_id, position_id, candidate_id, status, message, decided_by, decided_at }`  
**status:** `pending | accepted | rejected`

---

## Roles & Permissions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/roles/` | Создать роль 🔒 `{ name, description, security_level, permissions[] }` |
| GET | `/roles/` | Список ролей 🔒 |
| POST | `/roles/{name}/permissions` | Добавить permissions к роли 🔒 |
| DELETE | `/roles/{name}/permissions` | Удалить permissions из роли 🔒 |
| GET | `/project_roles/` | Список ролей для проектов |
| POST | `/permissions/` | Создать permission 🔒 `{ name }` |
| GET | `/permissions/` | Список permissions 🔒 |
| DELETE | `/permissions/{name}` | Удалить 🔒 |

---

## Sessions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sessions/` | Список сессий 🔒 (фильтры: user_id, is_active, ...) |
| DELETE | `/sessions/{id}` | Завершить сессию 🔒 |

---

## Pagination (везде где список)

Query params: `page` (default 1), `page_size` (1–100, default 20), `sort` (пример: `created_at:desc,username:asc`)

Response: `{ items[], total, page, page_size }`

---

## Error Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable",
    "detail": {}
  },
  "status": 400,
  "request_id": "<uuid>",
  "timestamp": "<timestamp>"
}
```

### Коды ошибок

| Code | Status | Когда |
|------|--------|-------|
| `WRONG_LOGIN_DATA` | 400 | Неверный логин/пароль |
| `INVALID_TOKEN` | 403 | Токен невалиден |
| `EXPIRED_TOKEN` | 400 | Токен истёк |
| `PASSWORD_MISMATCH` | 400 | Пароли не совпадают |
| `DUPLICATE_USER` | 409 | Юзер уже существует |
| `DUPLICATE_ROLE` | 409 | Роль уже существует |
| `NOT_FOUND_USER` | 404 | Юзер не найден |
| `NOT_FOUND_ROLE` | 404 | Роль не найдена |
| `NOT_FOUND_PERMISSIONS` | 404 | Permissions не найдены |
| `NOT_FOUND_PROFILE` | 404 | Профиль не найден |
| `NOT_FOUND_PROJECT` | 404 | Проект не найден |
| `NOT_FOUND_OR_INACTIVE_SESSION` | 400/404 | Сессия не найдена или неактивна |
| `ACCESS_DENIED` | 403 | Нет прав (detail содержит нужные permissions) |
| `PROTECTED_PERMISSION` | 409 | Permission защищён от изменений |
| `LINKED_ANOTHER_USER_OAUTH` | 409 | OAuth уже привязан к другому юзеру |
| `OAUTH_STATE_NOT_FOUND` | 404 | OAuth state не найден |
| `NOT_EXIST_PROVIDER_OAUTH` | 400 | Провайдер OAuth не существует |
| `INVALID_ROLE_NAME` | 400 | Недопустимое имя роли |
| `VALIDATION_EXCEPTION` | 422 | Ошибка валидации (detail — массив с loc/msg/type) |

---

## Notes

- 🔒 = требует `Authorization: Bearer <access_token>`
- Username: 4–100 символов, только `a-zA-Z0-9 ,.'- `
- Password: 8–128 символов
- Position ID и Application ID — **UUID**, User/Project/Session ID — **integer**
- Avatar upload: сначала `/presign` → загрузка на S3 → `/upload_complete`
