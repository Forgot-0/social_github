# 📊 Load Test — SLA & Run Guide

## Установка

```bash
pip install locust faker
```

---

## Запуск

### UI-режим (рекомендуется для начала)
```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10
# Открыть http://localhost:8089
```

### Headless (CI/CD)
```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users=200 \
  --spawn-rate=20 \
  --run-time=2m \
  --headless \
  --csv=results/load_test
```

### Только определённые классы пользователей
```bash
# Только чаты + сообщения
locust -f locustfile.py --host=http://localhost:8000 \
  --users=50 --spawn-rate=5 \
  ChatUser

# Только аутентификация
locust -f locustfile.py --host=http://localhost:8000 \
  --users=30 --spawn-rate=3 \
  AuthUser
```

---

## Профили нагрузки

| Класс пользователя | Вес | RPS цель | Описание |
|---|---|---|---|
| `ReadUser` | 4 | 200 | Просмотр профилей, пользователей |
| `ProjectUser` | 3 | 150 | Проекты, позиции, заявки |
| `ChatUser` | 3 | 100 | Чаты, сообщения |
| `AuthUser` | 1 | 50 | Логин, рефреш |
| `AdminUser` | 1 | 20 | Роли, сессии, управление |

При `--users=200` распределение по весам даст ~33 ReadUser, ~25 ProjectUser и т.д.

---

## SLA по эндпоинтам (P95)

### 🔐 Аутентификация — цель: **P95 < 300 ms**

| Эндпоинт | P95 | Почему |
|---|---|---|
| `POST /auth/login` | 300 ms | bcrypt + сессия в БД |
| `POST /auth/refresh` | 200 ms | проверка JWT + обновление cookie |
| `GET /users/me` | 150 ms | простой SELECT по токену |

### 👤 Пользователи и профили — цель: **P95 < 200 ms**

| Эндпоинт | P95 | Почему |
|---|---|---|
| `GET /users/me` | 150 ms | SELECT по user_id |
| `GET /users/` | 250 ms | SELECT с JOIN roles+permissions+sessions |
| `GET /profiles/` | 200 ms | SELECT + пагинация |
| `GET /profiles/{id}` | 150 ms | SELECT + contacts + avatars |
| `GET /users/sessions` | 150 ms | SELECT sessions по user_id |

### 🗂️ Проекты и позиции — цель: **P95 < 250 ms**

| Эндпоинт | P95 | Почему |
|---|---|---|
| `GET /projects/` | 200 ms | SELECT + memberships |
| `GET /projects/my` | 200 ms | SELECT с фильтром по user_id |
| `GET /projects/{id}` | 250 ms | SELECT + JOIN memberships |
| `POST /projects/` | 400 ms | INSERT + slug-проверка |
| `GET /positions/` | 200 ms | SELECT + фильтры |
| `GET /positions/{id}` | 150 ms | SELECT по UUID |
| `PUT /positions/{id}` | 300 ms | UPDATE + права |
| `DELETE /positions/{id}` | 300 ms | DELETE + каскад |
| `GET /applications/me` | 200 ms | SELECT по candidate_id |
| `POST /positions/{id}/applications` | 400 ms | INSERT + дедупликация |

### 💬 Чаты — цель: **P95 < 300 ms**

| Эндпоинт | P95 | Почему |
|---|---|---|
| `POST /chats/` | 400 ms | INSERT + добавление участников |
| `GET /chats/my` | 300 ms | cursor-пагинация + unread_count |
| `GET /chats/{id}` | 250 ms | SELECT + members |
| `PUT /chats/{id}` | 300 ms | UPDATE + проверка прав |
| `GET /chats/{id}/presence` | 150 ms | Redis lookup |
| `POST /chats/{id}/members` | 300 ms | INSERT + лимит-проверка |
| `DELETE /chats/{id}/members/{id}` | 250 ms | DELETE + WS-событие |
| `POST /chats/{id}/leave` | 250 ms | DELETE + owner-guard |

### 📨 Сообщения — цель: **P95 < 400 ms**

| Эндпоинт | P95 | Почему |
|---|---|---|
| `GET /chats/{id}/messages` | 350 ms | cursor + attachments + read_cursors |
| `POST /chats/{id}/messages` | 400 ms | INSERT + WS broadcast + delivery |
| `POST /chats/{id}/messages/upload` | 500 ms | presign S3 на каждый файл |
| `PUT /{id}/messages/{id}` | 300 ms | UPDATE + WS broadcast |
| `DELETE /{id}/messages/{id}` | 250 ms | soft-delete + WS broadcast |
| `POST /messages/read` | 150 ms | UPDATE cursor + WS broadcast |
| `POST /messages/forward` | 400 ms | INSERT + copy attachments ref |
| `GET /messages/read-details` | 250 ms | cursor-пагинация |
| `GET /{id}/attachments/{id}/url` | 200 ms | presign S3 GET (кеш 5 мин) |

### 🔑 Роли и права — цель: **P95 < 300 ms**

| Эндпоинт | P95 | Почему |
|---|---|---|
| `GET /roles/` | 200 ms | SELECT + JOIN permissions |
| `GET /permissions/` | 150 ms | простой SELECT |
| `POST /roles/` | 400 ms | INSERT + валидация дублей |
| `GET /project_roles/` | 150 ms | небольшая таблица |

---

## Разбор результатов

После `--headless --csv=results/load_test` появятся файлы:

```
results/load_test_stats.csv         ← RPS, latency по каждому эндпоинту
results/load_test_failures.csv      ← все ошибки
results/load_test_stats_history.csv ← динамика по времени
```

### Ключевые метрики для проверки

```
50th percentile (median) — типичный пользователь
95th percentile (P95)    — SLA-граница (смотрим сюда)
99th percentile (P99)    — выбросы, edge cases
Failure rate             — цель: < 0.1%
RPS (requests/sec)       — реальная пропускная способность
```

### Когда что означает

| Симптом | Вероятная причина |
|---|---|
| P95 > SLA только у `/auth/login` | Медленный bcrypt / нет connection pool |
| P95 > SLA у всех чатов | N+1 на members / нет индекса |
| P95 > SLA у `/messages` на пике | WS broadcast блокирует HTTP |
| Ошибки 503/504 | Нет autoscaling / исчерпан пул воркеров |
| Ошибки 429 | Сработал rate-limit (нормально для auth) |

---

## Рекомендуемые сценарии

```bash
# 1. Smoke test — убеждаемся что всё работает
locust -f locustfile.py --host=http://localhost:8000 \
  --users=10 --spawn-rate=2 --run-time=1m --headless

# 2. Load test — целевая нагрузка
locust -f locustfile.py --host=https://api.windoweropu.store \
  --users=200 --spawn-rate=20 --run-time=5m --headless \
  --csv=results/load

# 3. Stress test — ищем точку отказа
locust -f locustfile.py --host=https://api.windoweropu.store \
  --users=1000 --spawn-rate=50 --run-time=10m --headless \
  --csv=results/stress

# 4. Soak test — проверка утечек памяти
locust -f locustfile.py --host=http://localhost:8000 \
  --users=100 --spawn-rate=5 --run-time=1h --headless \
  --csv=results/soak
```
