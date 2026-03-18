# Руководство по интеграции API

Этот документ описывает, как интегрировать реальный бэкенд в приложение ProjectHub.

## Текущее состояние

На данный момент приложение работает с моковыми данными, но подготовлено для интеграции с реальным API.

## Структура API клиента

API клиент находится в `/src/app/services/api.ts` и содержит:

### Реализованные endpoints (из вашего API)

1. **Аутентификация** (`authApi`)
   - `POST /api/v1/auth/login` - Вход пользователя
   - `POST /api/v1/users/register` - Регистрация
   - `POST /api/v1/auth/logout` - Выход
   - `POST /api/v1/auth/refresh` - Обновление токена

2. **Пользователи** (`usersApi`)
   - `GET /api/v1/users/me` - Получить текущего пользователя
   - `GET /api/v1/users/` - Список пользователей с фильтрацией

### Endpoints, которые нужно добавить в бэкенд




## Схемы данных для новых endpoints

### Project Schema
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "goals": "string",
  "progress": "string",
  "owner_id": "integer",
  "tags": ["string"],
  "status": "active" | "paused" | "completed",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Position Schema
```json
{
  "id": "string",
  "project_id": "string",
  "title": "string",
  "description": "string",
  "required_skills": ["skill_id"],
  "status": "open" | "closed",
  "created_at": "datetime"
}
```

### Application Schema
```json
{
  "id": "string",
  "position_id": "string",
  "user_id": "integer",
  "message": "string",
  "status": "pending" | "accepted" | "rejected",
  "created_at": "datetime"
}
```

### Skill Schema
```json
{
  "id": "string",
  "name": "string",
  "category": "frontend" | "backend" | "design" | "management" | "data" | "marketing" | "other"
}
```

## Шаги для интеграции

### 1. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 2. Замена моковых данных на реальные API вызовы

#### Пример: HomePage.tsx

**Текущий код (с моками):**
```typescript
import { MOCK_PROJECTS } from '../data/mockData';

export function HomePage() {
  const filteredProjects = MOCK_PROJECTS.filter(...);
  // ...
}
```

**После интеграции:**
```typescript
import { useState, useEffect } from 'react';
import { projectsApi } from '../services/api';

export function HomePage() {
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchProjects() {
      try {
        const data = await projectsApi.getProjects({
          page: 1,
          page_size: 20,
        });
        setProjects(data.items);
      } catch (error) {
        console.error('Error fetching projects:', error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchProjects();
  }, []);

  // ... rest of component
}
```

### 3. Обработка аутентификации

API уже настроен для работы с JWT токенами:

```typescript
// При логине
const response = await authApi.login(username, password);
setAccessToken(response.access_token); // Сохраняет в localStorage

// При запросах
// Токен автоматически добавляется в заголовок Authorization
```

### 4. Обработка ошибок

Все API ошибки возвращают стандартный формат:

```typescript
try {
  await projectsApi.createProject(data);
} catch (error: any) {
  if (error?.error?.code === 'ACCESS_DENIED') {
    toast.error('Доступ запрещен');
  } else if (error?.error?.code === 'NOT_FOUND_PROJECT') {
    toast.error('Проект не найден');
  }
}
```

### 5. Автоматическое обновление токена

Добавьте interceptor для автоматического обновления токена:

```typescript
// В api.ts добавьте перед apiRequest:
async function refreshTokenIfNeeded(error: any) {
  if (error?.error?.code === 'EXPIRED_TOKEN') {
    try {
      const newToken = await authApi.refreshToken();
      setAccessToken(newToken.access_token);
      return true; // Токен обновлен, повторить запрос
    } catch {
      clearAccessToken();
      window.location.href = '/login';
      return false;
    }
  }
  return false;
}
```

## Тестирование

### Локальное тестирование с бэкендом

1. Запустите бэкенд сервер на `http://localhost:8000`
2. Убедитесь, что CORS настроен правильно
3. Запустите фронтенд: `npm run dev`
4. Проверьте Network tab в DevTools

### Полезные curl команды

```bash
# Логин
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo123"

# Получить текущего пользователя
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Создать проект (после реализации)
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Project",
    "description": "Description",
    "goals": "Goals",
    "tags": ["test"]
  }'
```

## Приоритеты реализации backend endpoints

1. **Высокий приоритет:**
   - Projects CRUD
   - Positions CRUD
   - Skills (список)
   
2. **Средний приоритет:**
   - Applications CRUD
   - User skills management
   - Recommendations engine

3. **Низкий приоритет:**
   - Analytics
   - Notifications
   - Advanced search

## Файлы, которые нужно обновить после реализации API

- [ ] `/src/app/pages/HomePage.tsx` - загрузка проектов
- [ ] `/src/app/pages/ProjectDetailPage.tsx` - детали проекта
- [ ] `/src/app/pages/CreateProjectPage.tsx` - создание проекта
- [ ] `/src/app/pages/MyProjectsPage.tsx` - мои проекты
- [ ] `/src/app/pages/ProfilePage.tsx` - профиль пользователя
- [ ] `/src/app/pages/SettingsPage.tsx` - навыки пользователя
- [ ] `/src/app/services/api.ts` - реализовать заглушки

## Контакты

При возникновении вопросов по интеграции обращайтесь к этому документу.
