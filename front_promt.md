Ты — senior frontend-инженер и архитектор. Твоя задача — сгенерировать **готовый фронтенд-проект** (TypeScript) для приложения моего бэкенд приложения на базе фреймворка Next.js, **целиком** основанный на спецификации OpenAPI JSON по адресу/файлу openapi.json. Выведи структуру проекта, инструкции по запуску, настройки codegen, CI, примеры кода и объяснения архитектурных решений.

Требования (строго):

1. Язык и инструменты
   - TypeScript, React. Next.js (app router или pages — выбери app-router если нет жесткого ограничения).
   - Bundler: встроенный (Next.js).
   - State & Server-state: React Query (TanStack Query) для всех запросов к API.
   - HTTP-клиент: Axios (или fetch wrapper) с типизированным клиентом, сгенерированным по OpenAPI.
   - Codegen: используй openapi-generator.
   - Styling: TailwindCSS.
   - Testing: Vitest + React Testing Library для unit; Playwright для e2e.
   - Lint/Format: ESLint + Prettier + TypeScript strict.

2. OpenAPI + типы
   - Сгенерируй типизированный API-клиент из openapi.json и помести в `packages/api` или `src/api`.
   - Для каждого endpoint-а сгенерируй React Query hooks (get/post/... -> useXQuery/useXMutation) автоматически или вручную показать шаблон генерации.
   - Докажи, что типы запроса/ответа используются в компонентах.

3. Аутентификация — обязательно (подход под ваш серверный менеджер refresh cookie)
   - Подразумевается сервер ставит `refresh_token` в HttpOnly/secure cookie (имя: `refresh_token`) и отдаёт `access_token` в теле ответа при логине/refresh. Не пытаться читать HttpOnly cookie из JS.
   - Frontend должен:
     a) Хранить `access_token` только в памяти (React context / singleton) — **не** в localStorage/sessionStorage.
     b) При каждом запросе прикреплять `Authorization: Bearer <access_token>`.
     c) При 400 (access expired) автоматически вызвать `/auth/refresh` (или endpoint из OpenAPI) с `credentials: 'include'` (или axios `{ withCredentials: true }`) чтобы сервер прочитал refresh cookie и вернул новый access token. Затем повторить исходный запрос.
     d) Обработать параллельные 400 запросы корректно — реализовать очередь запросов (single-refresh-in-flight).
     e) Логаут: вызвать `/auth/logout` (если есть) и очистить access token в памяти; удалить cookie — ожидается серверная логика удаления cookie, но также показать фронтендный `delete` (fetch) с `credentials: 'include'`.
   - Включи примеры кода: `axios` instance с interceptor-ом + `AuthProvider` (React Context) + `useAuth` hook + `ProtectedRoute` HOC / middleware для Next.js (getServerSideProps/app-router middleware).
   - Для SSR (Next.js) укажи паттерн: на сервере использовать endpoint `/auth/refresh` (server-side fetch with credentials) для получения access token и затем рендерить страницу; избегать чтения HttpOnly cookie в клиентском JS.

4. Архитектура и структура репозитория
   - Предложи monorepo (pnpm/turborepo) с пакетами `apps/frontend`, `packages/api-client`, `packages/ui`, `packages/hooks`.
   - Или маленький repo: `src/` с `api/`, `lib/`, `features/`, `components/`, `pages/`/`app/`, `styles/`.
   - Приложи пример структуры файлов (tree).

5. Безопасность
   - Подчеркни: HttpOnly refresh cookie + access token в памяти, CSRF: если используешь cookies для auth, опиши защиту (sameSite=strict, либо CSRF-token flow). Если сервер использует SameSite strict+HttpOnly, укажи как это влияет.
   - Включи заголовки безопасности (CSP, X-Frame-Options) рекомендации на фронтенде/сервере.

6. Документация и примеры
   - Сгенерируй README с шагами: setup, generate api, dev, build, test, env vars.
   - Приведи пример компонента `Dashboard` который использует generated hook `useGetItemsQuery` и обеспечивает авторизацию.
   - Пример E2E теста Playwright, проверяющий логин, автоматический refresh и доступ к защищённой странице.

7. Дополнительно
   - Дай шаблон `axios` interceptor-а с логикой refresh (и обработкой race conditions).
   - Дай пример `AuthProvider` (полный TypeScript код).
   - Дай пример `getServerSideProps` / Next.js middleware для защитённых страниц.
   - Выведи список ожиданий: какие env vars требуются (API_URL, NEXT_PUBLIC_API_URL, NODE_ENV).
   - В конце — краткий чек-лист для ревью безопасности.

Вывод:
- Сгенерируй архив/репо skeleton (tree), инструкции для запуска, codegen-команды и все необходимые исходные файлы/фрагменты кода (AuthProvider, axios instance, примеры компонентов, тесты, CI workflow, README).
- Комментируй ключевые места (почему solution безопасен, как работает refresh flow).
- Если OpenAPI не содержит auth endpoints, добавь шаблонные endpoint-ы `/auth/login`, `/auth/refresh`, `/auth/logout` и опиши ожидаемые request/response типы.

Важное: используйте в примерах именно поведение, соответствующее `IRefreshTokenCookieManager`:
- refresh cookie имя — `refresh_token`
- cookie — HttpOnly, Secure, SameSite=strict, path `/`
- Frontend не читает cookie напрямую; при refresh-запросе посылает credentials и сервер читает cookie.

Сгенерируй результат на русском языке. Конец промпта.