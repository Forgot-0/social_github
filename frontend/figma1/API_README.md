# 🔌 API Integration - Complete Guide

> Полное руководство по интеграции типизированного API с автоматическим refresh и безопасной аутентификацией

## 📚 Документация

- **[SECURITY.md](./SECURITY.md)** - Подробная документация по безопасности и аутентификации
- **[API_USAGE.md](./API_USAGE.md)** - Руководство по использованию API и React Query hooks
- **[API_INTEGRATION.md](./API_INTEGRATION.md)** - Интеграция с backend

## 🎯 Что реализовано

### ✅ Типизированный API клиент

- ✨ **Auto-generated types** из OpenAPI spec
- 🔒 **Type-safe** методы для всех endpoints
- 📦 **Organized** по модулям (auth, users, permissions)

### ✅ React Query Hooks

- 🎣 **Custom hooks** для каждого endpoint
- 🔄 **Automatic caching** и refetching
- ⚡ **Optimistic updates**
- 🗂️ **Query key factories**

### ✅ Безопасная аутентификация

- 🔐 **Access token в памяти** (не localStorage!)
- 🍪 **Refresh token в HttpOnly cookie**
- 🔄 **Автоматический refresh** при истечении
- 🚦 **Request queue** для параллельных запросов
- 🛡️ **XSS защита** - токены недоступны из JS
- 🛡️ **CSRF защита** - SameSite cookies

### ✅ Developer Experience

- 📖 **Подробная документация**
- 💡 **Примеры использования**
- 🔍 **Error handling** с type safety
- 🎨 **AuthProvider** и **ProtectedRoute**

## 📁 Структура файлов

```
/src/api/
├── types.ts                 # TypeScript типы из OpenAPI
├── tokenManager.ts          # Управление access token (память!)
├── axiosInstance.ts         # Axios с interceptors и auto-refresh
├── client.ts                # Типизированный API клиент
├── hooks/                   # React Query hooks
│   ├── useAuth.ts          # Auth mutations
│   ├── useUsers.ts         # Users queries/mutations
│   ├── usePermissions.ts   # Permissions queries/mutations
│   └── index.ts            # Central export
├── auth/                    # Auth Context и Protected Routes
│   ├── AuthContext.tsx     # React Context для auth
│   ├── ProtectedRoute.tsx  # HOC для защищенных роутов
│   └── index.ts
└── index.ts                 # Main export

Документация:
├── SECURITY.md              # Безопасность (ОБЯЗАТЕЛЬНО ПРОЧИТАТЬ!)
├── API_USAGE.md             # Примеры использования
└── API_README.md            # Этот файл
```

## 🚀 Быстрый старт

### 1. Установка (уже сделано)

```bash
# Пакеты уже установлены:
# - @tanstack/react-query
# - axios
```

### 2. Настройка окружения

```bash
# Скопируйте .env.example
cp .env.example .env

# Отредактируйте .env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Использование в коде

```typescript
// В любом компоненте
import { useAuth, useMeQuery, useLoginMutation } from '../api';

function MyComponent() {
  const { user, isAuthenticated, logout } = useAuth();
  const { data: userData } = useMeQuery();
  
  if (!isAuthenticated) {
    return <div>Please login</div>;
  }
  
  return (
    <div>
      <h1>Welcome, {user?.username}!</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

## 🔐 Аутентификация

### Архитектура

```
┌─────────────┐
│   Frontend  │
│             │
│ Access Token│ ← В ПАМЯТИ (tokenManager)
│ в памяти    │
└──────┬──────┘
       │
       │ Authorization: Bearer <token>
       │
       ▼
┌─────────────┐
│   Backend   │
│             │
│Refresh Token│ ← В HttpOnly Cookie
│   в cookie  │
└─────────────┘
```

### Поток работы

1. **Login**: `POST /api/v1/auth/login`
   - Сервер возвращает `access_token` в JSON
   - Сервер ставит `refresh_token` в HttpOnly cookie
   - Frontend сохраняет `access_token` **только в памяти**

2. **Запросы**: каждый запрос включает `Authorization: Bearer <access_token>`

3. **Auto-refresh**: при истечении токена (400/EXPIRED_TOKEN)
   - Axios interceptor ловит ошибку
   - Вызывает `POST /api/v1/auth/refresh` с `withCredentials: true`
   - Сервер читает `refresh_token` из cookie
   - Возвращает новый `access_token`
   - Повторяет исходный запрос

4. **Logout**: `POST /api/v1/auth/logout`
   - Очищает `access_token` из памяти
   - Сервер удаляет `refresh_token` cookie

### ВАЖНО: Безопасность

**❌ НЕ ДЕЛАЙТЕ:**
```typescript
// ❌ НЕТ localStorage!
localStorage.setItem('token', accessToken);

// ❌ НЕТ sessionStorage!
sessionStorage.setItem('token', accessToken);

// ❌ НЕ пытайтесь читать HttpOnly cookie!
const token = document.cookie; // Не содержит refresh_token
```

**✅ ДЕЛАЙТЕ:**
```typescript
// ✅ Token Manager хранит токен в памяти
import { tokenManager } from './api/tokenManager';

// ✅ При login
tokenManager.setAccessToken(response.access_token);

// ✅ При logout
tokenManager.clearAccessToken();
```

Подробнее: [SECURITY.md](./SECURITY.md)

## 📦 API клиент

### Прямое использование

```typescript
import { apiClient } from '../api';

// Auth
const response = await apiClient.auth.login({ username, password });
await apiClient.auth.logout();

// Users
const user = await apiClient.users.getMe();
const users = await apiClient.users.getUsers({ page: 1, page_size: 20 });
await apiClient.users.register(userData);

// Permissions
const perms = await apiClient.permissions.getPermissions();
```

### Через React Query (рекомендуется)

```typescript
import { useMeQuery, useUsersQuery, useLoginMutation } from '../api';

function Component() {
  // Queries (GET)
  const { data: me } = useMeQuery();
  const { data: users } = useUsersQuery({ page: 1 });

  // Mutations (POST/PUT/DELETE)
  const login = useLoginMutation();
  login.mutate({ username: 'demo', password: 'demo' });
}
```

Подробнее: [API_USAGE.md](./API_USAGE.md)

## 🎣 React Query Hooks

### Queries (GET запросы)

| Hook | Описание |
|------|----------|
| `useMeQuery()` | Получить текущего пользователя |
| `useUsersQuery(params)` | Список пользователей с фильтрами |
| `useSessionsQuery()` | Активные сессии пользователя |
| `usePermissionsQuery(params)` | Список прав доступа |

### Mutations (POST/PUT/DELETE)

| Hook | Описание |
|------|----------|
| `useLoginMutation()` | Вход в систему |
| `useLogoutMutation()` | Выход из системы |
| `useRegisterMutation()` | Регистрация |
| `useSendVerificationCodeMutation()` | Отправить код верификации |
| `useVerifyEmailMutation()` | Подтвердить email |
| `useSendPasswordResetCodeMutation()` | Отправить код сброса пароля |
| `useResetPasswordMutation()` | Сбросить пароль |
| `useAssignRoleMutation()` | Назначить роль |
| `useRemoveRoleMutation()` | Удалить роль |
| `useAddPermissionsMutation()` | Добавить права |
| `useRemovePermissionsMutation()` | Удалить права |
| `useCreatePermissionMutation()` | Создать право |
| `useDeletePermissionMutation()` | Удалить право |

## 🛠 Примеры

### Пример 1: Login форма

```typescript
import { useAuth } from '../api';

function LoginForm() {
  const { login } = useAuth();
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(credentials);
      // Success - автоматический редирект в AuthContext
    } catch (error) {
      // Error handling в AuthContext
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* inputs */}
    </form>
  );
}
```

### Пример 2: Защищенная страница

```typescript
import { ProtectedRoute } from '../api';

// В routes.tsx
const routes = [
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    ),
  },
];
```

### Пример 3: Профиль пользователя

```typescript
import { useMeQuery } from '../api';

function ProfilePage() {
  const { data: user, isLoading, refetch } = useMeQuery();

  if (isLoading) return <Spinner />;

  return (
    <div>
      <h1>{user.username}</h1>
      <p>{user.email}</p>
      <button onClick={() => refetch()}>Обновить</button>
    </div>
  );
}
```

### Пример 4: Список пользователей с пагинацией

```typescript
import { useUsersQuery } from '../api';

function UsersPage() {
  const [page, setPage] = useState(1);
  
  const { data, isLoading } = useUsersQuery({
    page,
    page_size: 20,
    is_active: true,
  });

  return (
    <div>
      {data?.items.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
      
      <Pagination
        current={page}
        total={data?.total_pages}
        onChange={setPage}
      />
    </div>
  );
}
```

Больше примеров: [API_USAGE.md](./API_USAGE.md)

## ❌ Обработка ошибок

### Type-safe обработка

```typescript
import { ErrorCode } from '../api';

const mutation = useLoginMutation({
  onError: (error) => {
    const code = error.response?.data?.error?.code;
    
    switch (code) {
      case ErrorCode.WRONG_LOGIN_DATA:
        toast.error('Неверный логин или пароль');
        break;
      case ErrorCode.DUPLICATE_USER:
        toast.error('Пользователь уже существует');
        break;
      default:
        toast.error('Произошла ошибка');
    }
  },
});
```

### Все коды ошибок

```typescript
export enum ErrorCode {
  WRONG_LOGIN_DATA = 'WRONG_LOGIN_DATA',
  INVALID_TOKEN = 'INVALID_TOKEN',
  EXPIRED_TOKEN = 'EXPIRED_TOKEN',
  NOT_FOUND_USER = 'NOT_FOUND_USER',
  PASSWORD_MISMATCH = 'PASSWORD_MISMATCH',
  DUPLICATE_USER = 'DUPLICATE_USER',
  ACCESS_DENIED = 'ACCESS_DENIED',
  // ... и другие
}
```

## 🔄 Автоматический Refresh

### Как это работает

1. Access token истекает
2. Запрос возвращает `400 EXPIRED_TOKEN`
3. Axios interceptor ловит ошибку
4. Вызывает `POST /api/v1/auth/refresh` с `withCredentials: true`
5. Сервер читает refresh_token из HttpOnly cookie
6. Возвращает новый access_token
7. Сохраняет в памяти
8. **Повторяет исходный запрос автоматически**

### Параллельные запросы

Если несколько запросов одновременно получают 400:
- Только **один** refresh запрос
- Остальные запросы ждут в **очереди**
- После успешного refresh все повторяются

```typescript
// В axiosInstance.ts
let isRefreshing = false;
let failedQueue = [];

// При refresh
if (isRefreshing) {
  // Добавляем в очередь
  return new Promise((resolve, reject) => {
    failedQueue.push({ resolve, reject });
  });
}
```

## 🌐 Backend Requirements

### Обязательные настройки

#### 1. CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com"],
    allow_credentials=True,  # КРИТИЧНО!
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. Cookie настройки

```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,      # НЕ читается из JS
    secure=True,        # Только HTTPS (prod)
    samesite="strict",  # CSRF защита
    max_age=7*24*60*60, # 7 дней
    path="/"
)
```

#### 3. Endpoints

- `POST /api/v1/auth/login` - возвращает access_token, ставит refresh cookie
- `POST /api/v1/auth/refresh` - читает refresh cookie, возвращает новый access_token
- `POST /api/v1/auth/logout` - удаляет refresh cookie

## 📝 Checklist

Перед деплоем убедитесь:

- [ ] `.env` файл создан с правильным `VITE_API_BASE_URL`
- [ ] Backend CORS настроен правильно
- [ ] `allow_credentials=True` в CORS
- [ ] Refresh cookie с `httponly=True`
- [ ] Refresh cookie с `secure=True` (production)
- [ ] Refresh cookie с `samesite=strict`
- [ ] Access token НЕ в localStorage/sessionStorage
- [ ] HTTPS в production
- [ ] Автоматический refresh работает
- [ ] Protected routes защищены
- [ ] Error handling настроен

## 🐛 Troubleshooting

### Access token пропадает при перезагрузке

**Это нормально!** Access token хранится в памяти и очищается при перезагрузке.

**Решение**: При загрузке приложения:
1. Проверяем есть ли access token в памяти
2. Если нет, вызываем `/auth/refresh`
3. Получаем новый access token из refresh cookie

Это уже реализовано в `AuthContext.tsx`:

```typescript
useEffect(() => {
  if (!tokenManager.isAuthenticated()) {
    // Пытаемся refresh
    authApi.refresh().then(/* ... */);
  }
}, []);
```

### CORS ошибки

```
Access to XMLHttpRequest blocked by CORS policy
```

**Решение**:
1. Проверьте `allow_credentials=True` в backend
2. Проверьте `withCredentials: true` в axios
3. Проверьте что домены совпадают

### Cookie не отправляется

```
refresh_token cookie not sent to server
```

**Решение**:
1. Убедитесь что `withCredentials: true`
2. Проверьте `samesite` настройки
3. В development используйте `localhost` (не `127.0.0.1`)
4. В production обязательно HTTPS

### Infinite refresh loop

```
Refresh keeps being called in loop
```

**Решение**:
1. Проверьте что refresh endpoint НЕ требует access token
2. Проверьте что `_retry` flag работает
3. Убедитесь что refresh возвращает 200, а не 400

## 📚 Дополнительные ресурсы

- [React Query Documentation](https://tanstack.com/query/latest)
- [Axios Documentation](https://axios-http.com/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

## 🎓 Следующие шаги

1. **Прочитайте [SECURITY.md](./SECURITY.md)** - ОБЯЗАТЕЛЬНО!
2. Изучите [API_USAGE.md](./API_USAGE.md) для примеров
3. Настройте `.env` файл
4. Запустите backend
5. Протестируйте login/logout
6. Проверьте автоматический refresh

---

**Вопросы?** Откройте issue на GitHub или обратитесь к документации.

**Сделано с ❤️ и заботой о безопасности** 🔐
