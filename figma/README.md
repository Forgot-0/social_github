# InCollab Frontend

Фронтенд подключён к API и не использует тестовые данные как fallback.

## Что настроено

- прямые запросы в `https://api.incollab.ru/api/v1`
- `credentials: include` для refresh token cookie
- логин отправляется корректным `FormData`
- страницы проектов, позиций и деталей проекта берут данные только из API
- локальный запуск рассчитан на то, что `http://localhost:5173` добавлен в CORS backend

## Быстрый старт

```bash
npm install
cp .env.example .env
npm run dev
```

После запуска сайт будет доступен на `http://localhost:5173`.

## Переменные окружения

```env
VITE_API_URL=https://api.incollab.ru/api/v1
```

## Что важно для локального запуска

На backend нужно разрешить origin `http://localhost:5173` и включить credentials для cookie refresh token.

## Сборка

```bash
npm run build
```
