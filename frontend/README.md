# SocialGH Frontend

Фронтенд-приложение на **Next.js 15 (App Router)** + **TypeScript** для платформы SocialGH — поиск проектов, команд и позиций.

## Стек технологий

| Категория | Инструмент |
|-----------|------------|
| Фреймворк | Next.js 15 (App Router) |
| Язык | TypeScript (strict) |
| Стили | Tailwind CSS |
| HTTP | Axios (withCredentials) |
| Server State | TanStack React Query v5 |
| Codegen | openapi-generator-cli |
| Unit-тесты | Vitest + React Testing Library |
| E2E-тесты | Playwright |
| Lint/Format | ESLint + Prettier |
| CI | GitHub Actions |

---

## Быстрый старт

### 1. Установка зависимостей

```bash
cd frontend
npm install
```

### 2. Переменные окружения

```bash
cp .env.example .env.local
```

Необходимые переменные:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `API_URL` | URL бэкенда (для SSR и rewrite) | `http://localhost:8000` |
| `NEXT_PUBLIC_API_URL` | URL API для клиента | `/api` (через rewrite) |
| `NODE_ENV` | Окружение | `development` |

### 3. Генерация API-клиента (опционально)

```bash
npm run generate-api
```

Генерирует типизированный клиент из `openapi.json` в `src/api/generated/`.

> **Примечание:** Типы уже продублированы в `src/types/index.ts` для работы без codegen.

### 4. Запуск dev-сервера

```bash
npm run dev
```

Приложение доступно на [http://localhost:3000](http://localhost:3000).

### 5. Сборка для продакшена

```bash
npm run build
npm start
```

---

## Структура проекта

```
frontend/
├── .github/workflows/ci.yml   # GitHub Actions CI pipeline
├── .env.example                # Шаблон переменных окружения
├── next.config.ts              # Next.js конфиг + rewrite + security headers
├── tailwind.config.ts          # Tailwind конфигурация
├── vitest.config.ts            # Vitest конфигурация
├── playwright.config.ts        # Playwright E2E конфигурация
├── src/
│   ├── api/
│   │   ├── client.ts           # Axios instance с refresh interceptor
│   │   ├── generated/          # Сгенерированный API-клиент (gitignored)
│   │   └── hooks/              # React Query хуки для всех endpoints
│   │       ├── auth.ts         # login, logout, refresh, verify, reset
│   │       ├── users.ts        # register, me, roles, permissions
│   │       ├── profiles.ts     # CRUD профилей, аватары, контакты
│   │       ├── projects.ts     # CRUD проектов, участники
│   │       ├── positions.ts    # CRUD позиций
│   │       ├── applications.ts # Заявки: подача, одобрение, отклонение
│   │       ├── sessions.ts     # Управление сессиями
│   │       ├── roles.ts        # CRUD ролей
│   │       └── permissions.ts  # CRUD разрешений
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx          # Root layout (Providers + Header + Footer)
│   │   ├── page.tsx            # Landing page
│   │   ├── providers.tsx       # QueryClient + AuthProvider
│   │   ├── (auth)/login/       # Страница входа
│   │   ├── (auth)/register/    # Страница регистрации
│   │   ├── dashboard/          # Панель пользователя (protected)
│   │   ├── projects/new/       # Создание проекта (protected)
│   │   ├── projects/[id]/      # Детали проекта
│   │   ├── positions/          # Список открытых позиций
│   │   ├── profile/            # Профиль (protected)
│   │   ├── profile/edit/       # Редактирование профиля (protected)
│   │   └── settings/sessions/  # Управление сессиями (protected)
│   ├── components/
│   │   ├── auth/ProtectedRoute.tsx  # HOC для защиты страниц
│   │   ├── layout/Header.tsx        # Навигация
│   │   ├── layout/Footer.tsx        # Футер
│   │   └── ui/                      # UI примитивы (Spinner, Badge)
│   ├── lib/
│   │   ├── auth/AuthProvider.tsx     # React Context для аутентификации
│   │   ├── auth/useAuth.ts          # Хук для доступа к auth контексту
│   │   ├── auth/token-manager.ts    # In-memory хранение access_token
│   │   └── utils.ts                 # cn(), formatDate(), formatDateTime()
│   ├── middleware.ts            # Next.js Edge Middleware (проверка cookie)
│   ├── styles/globals.css       # Tailwind + кастомные CSS компоненты
│   └── types/index.ts           # Все TypeScript типы из OpenAPI
└── tests/
    ├── setup.ts                 # Vitest setup
    ├── unit/                    # Unit-тесты
    └── e2e/                     # Playwright E2E-тесты
```

---

## Архитектура аутентификации

### Модель безопасности

```
┌─────────────┐                  ┌──────────────┐
│   Browser    │                  │   Backend    │
│              │                  │   (FastAPI)  │
│  ┌────────┐  │   POST /login   │              │
│  │ Login  │──┼────────────────▶│  Проверяет   │
│  │ Form   │  │                  │  credentials │
│  └────────┘  │◀────────────────│              │
│              │  access_token    │  Ставит      │
│  ┌────────┐  │  (в теле)       │  refresh_token│
│  │ Memory │  │  + Set-Cookie:  │  (HttpOnly,  │
│  │ Store  │  │  refresh_token  │  Secure,     │
│  └────────┘  │  (HttpOnly)     │  SameSite=   │
│              │                  │  strict)     │
└─────────────┘                  └──────────────┘
```

**Ключевые принципы:**

1. **access_token хранится только в памяти** (переменная `tokenManager`), НЕ в localStorage/sessionStorage
2. **refresh_token** — HttpOnly Secure cookie, SameSite=strict, path=/. JavaScript не имеет к нему доступа
3. При каждом запросе: `Authorization: Bearer <access_token>`
4. При получении 401: автоматический вызов `POST /auth/refresh` с `credentials: 'include'`
5. **Single-flight refresh**: параллельные 401 запросы ставятся в очередь, refresh выполняется один раз

### Refresh Flow (Axios Interceptor)

```
Request → 401 → Уже идёт refresh?
                 ├─ Да → Ставим запрос в очередь → Ждём новый token → Повтор
                 └─ Нет → POST /auth/refresh (withCredentials)
                           ├─ Успех → Сохраняем token → Повторяем все запросы из очереди
                           └─ Ошибка → Очищаем token → Redirect /login
```

### SSR / Middleware

**Next.js Edge Middleware** (`src/middleware.ts`):
- Проверяет **наличие** `refresh_token` cookie (не читает значение)
- Защищённые пути: `/dashboard`, `/profile`, `/settings`, `/projects/new`
- Не авторизован + защищённый путь → redirect `/login?redirect=...`
- Авторизован + страница логина → redirect `/dashboard`

---

## Команды

| Команда | Описание |
|---------|----------|
| `npm run dev` | Dev-сервер (localhost:3000) |
| `npm run build` | Production build |
| `npm start` | Запуск production build |
| `npm run lint` | ESLint проверка |
| `npm run lint:fix` | ESLint авто-исправление |
| `npm run format` | Prettier форматирование |
| `npm run format:check` | Проверка форматирования |
| `npm run type-check` | TypeScript проверка типов |
| `npm test` | Unit-тесты (Vitest) |
| `npm run test:watch` | Unit-тесты в watch-режиме |
| `npm run test:coverage` | Unit-тесты с покрытием |
| `npm run test:e2e` | E2E-тесты (Playwright) |
| `npm run generate-api` | Генерация API-клиента из openapi.json |

---

## Безопасность — Чек-лист для ревью

- [x] **access_token** хранится ТОЛЬКО в памяти (не localStorage/sessionStorage)
- [x] **refresh_token** — HttpOnly, Secure, SameSite=strict cookie
- [x] Frontend НЕ читает значение HttpOnly cookie из JavaScript
- [x] Все API-запросы с `withCredentials: true` для передачи cookie
- [x] Axios interceptor с single-flight refresh и очередью запросов
- [x] Next.js middleware проверяет наличие cookie на Edge (не валидирует)
- [x] Security headers в `next.config.ts`: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- [x] CSRF защита: SameSite=strict cookie блокирует cross-origin запросы
- [x] При неуспешном refresh — полная очистка токена и redirect на /login
- [x] Пароли не кэшируются, передаются через form-urlencoded (OAuth2 стандарт)
- [x] Нет секретов в клиентском коде (NEXT_PUBLIC_ только для публичных значений)

---

## Заметки по разработке

### Добавление нового API endpoint

1. Добавьте типы в `src/types/index.ts`
2. Создайте React Query хук в соответствующем файле `src/api/hooks/`
3. Используйте хук в компоненте

### Пример использования хуков в компоненте

```tsx
"use client";

import { usePositionsQuery, useApplyToPositionMutation } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

function MyComponent() {
  const { data, isLoading } = usePositionsQuery({ page: 1, page_size: 10 });
  const apply = useApplyToPositionMutation();

  const handleApply = (positionId: string) => {
    apply.mutate({ positionId, body: { message: "Хочу присоединиться!" } });
  };

  if (isLoading) return <div>Загрузка...</div>;

  return (
    <ul>
      {data?.items.map((pos) => (
        <li key={pos.id}>
          {pos.title}
          <button onClick={() => handleApply(pos.id)}>Откликнуться</button>
        </li>
      ))}
    </ul>
  );
}

export default function Page() {
  return (
    <ProtectedRoute>
      <MyComponent />
    </ProtectedRoute>
  );
}
```
