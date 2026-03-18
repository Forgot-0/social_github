# Руководство по использованию API

## 📚 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Типизированный API клиент](#типизированный-api-клиент)
3. [React Query Hooks](#react-query-hooks)
4. [Аутентификация](#аутентификация)
5. [Обработка ошибок](#обработка-ошибок)
6. [Примеры использования](#примеры-использования)

---

## 🚀 Быстрый старт

### 1. Настройка окружения

```bash
# Создайте .env файл
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
```

### 2. Оберните приложение провайдерами

```typescript
// src/app/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../api/auth';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <YourApp />
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

### 3. Используйте hooks

```typescript
import { useAuth, useMeQuery } from '../api';

function Profile() {
  const { user } = useAuth();
  const { data, isLoading } = useMeQuery();

  if (isLoading) return <div>Loading...</div>;
  
  return <div>Hello, {data?.username}!</div>;
}
```

---

## 🔧 Типизированный API клиент

### Импорт

```typescript
import { apiClient } from '../api';
```

### Структура

```typescript
apiClient = {
  auth: {
    login(),
    logout(),
    refresh(),
    sendVerificationCode(),
    verifyEmail(),
    sendPasswordResetCode(),
    resetPassword(),
    getOAuthUrl(),
    getOAuthConnectUrl(),
  },
  users: {
    register(),
    getMe(),
    getUsers(),
    assignRole(),
    removeRole(),
    addPermissions(),
    removePermissions(),
    getSessions(),
  },
  permissions: {
    getPermissions(),
    createPermission(),
    deletePermission(),
  },
}
```

### Прямое использование

```typescript
// Если вам нужен прямой вызов (не через hooks)
const data = await apiClient.users.getMe();
```

---

## 🎣 React Query Hooks

### Auth Hooks

#### useLoginMutation

```typescript
import { useLoginMutation } from '../api';

function LoginForm() {
  const loginMutation = useLoginMutation({
    onSuccess: (data) => {
      console.log('Access token:', data.access_token);
      navigate('/');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error?.message);
    },
  });

  const handleSubmit = () => {
    loginMutation.mutate({
      username: 'demo',
      password: 'demo123',
    });
  };

  return (
    <button onClick={handleSubmit} disabled={loginMutation.isPending}>
      {loginMutation.isPending ? 'Logging in...' : 'Login'}
    </button>
  );
}
```

#### useLogoutMutation

```typescript
import { useLogoutMutation } from '../api';

function LogoutButton() {
  const logoutMutation = useLogoutMutation({
    onSuccess: () => {
      toast.success('Logged out successfully');
      navigate('/login');
    },
  });

  return (
    <button onClick={() => logoutMutation.mutate()}>
      Logout
    </button>
  );
}
```

#### Другие Auth Hooks

```typescript
// Email verification
const sendCodeMutation = useSendVerificationCodeMutation();
sendCodeMutation.mutate({ email: 'user@example.com' });

const verifyEmailMutation = useVerifyEmailMutation();
verifyEmailMutation.mutate({ token: 'verification-token' });

// Password reset
const resetCodeMutation = useSendPasswordResetCodeMutation();
resetCodeMutation.mutate({ email: 'user@example.com' });

const resetPasswordMutation = useResetPasswordMutation();
resetPasswordMutation.mutate({
  token: 'reset-token',
  password: 'newPassword123',
  repeat_password: 'newPassword123',
});

// OAuth
const oauthMutation = useGetOAuthUrlMutation();
oauthMutation.mutate('google'); // или 'github'
```

### User Hooks

#### useMeQuery (GET текущего пользователя)

```typescript
import { useMeQuery } from '../api';

function UserProfile() {
  const { data: user, isLoading, error, refetch } = useMeQuery();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>{user.username}</h1>
      <p>{user.email}</p>
      <button onClick={() => refetch()}>Refresh</button>
    </div>
  );
}
```

#### useUsersQuery (GET список пользователей)

```typescript
import { useUsersQuery } from '../api';

function UsersList() {
  const { data, isLoading } = useUsersQuery({
    page: 1,
    page_size: 20,
    is_active: true,
    sort: 'created_at:desc',
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Total users: {data.total}</h2>
      {data.items.map((user) => (
        <div key={user.id}>{user.username}</div>
      ))}
      <p>Page {data.page} of {data.total_pages}</p>
    </div>
  );
}
```

#### useRegisterMutation

```typescript
import { useRegisterMutation } from '../api';

function RegisterForm() {
  const registerMutation = useRegisterMutation({
    onSuccess: (user) => {
      toast.success('Registration successful!');
      console.log('New user:', user);
    },
    onError: (error) => {
      if (error.response?.data?.error?.code === 'DUPLICATE_USER') {
        toast.error('User already exists');
      }
    },
  });

  const handleRegister = () => {
    registerMutation.mutate({
      email: 'newuser@example.com',
      username: 'newuser',
      password: 'SecurePass123',
      repeat_password: 'SecurePass123',
    });
  };

  return (
    <button onClick={handleRegister}>
      Register
    </button>
  );
}
```

#### Управление ролями и правами

```typescript
import { 
  useAssignRoleMutation, 
  useRemoveRoleMutation,
  useAddPermissionsMutation,
  useRemovePermissionsMutation,
} from '../api';

function UserManagement({ userId }: { userId: number }) {
  const assignRole = useAssignRoleMutation();
  const removeRole = useRemoveRoleMutation();
  const addPermissions = useAddPermissionsMutation();
  const removePermissions = useRemovePermissionsMutation();

  return (
    <div>
      <button 
        onClick={() => assignRole.mutate({ 
          userId, 
          data: { role_name: 'admin' } 
        })}
      >
        Make Admin
      </button>

      <button 
        onClick={() => removeRole.mutate({ 
          userId, 
          roleName: 'admin' 
        })}
      >
        Remove Admin
      </button>

      <button 
        onClick={() => addPermissions.mutate({ 
          userId, 
          data: { permissions: ['read', 'write'] } 
        })}
      >
        Add Permissions
      </button>
    </div>
  );
}
```

#### useSessionsQuery

```typescript
import { useSessionsQuery } from '../api';

function ActiveSessions() {
  const { data: sessions } = useSessionsQuery();

  return (
    <div>
      <h2>Active Sessions</h2>
      {sessions?.map((session) => (
        <div key={session.id}>
          <p>Device: {session.device}</p>
          <p>IP: {session.ip_address}</p>
          <p>Last activity: {session.last_activity}</p>
        </div>
      ))}
    </div>
  );
}
```

### Permission Hooks

#### usePermissionsQuery

```typescript
import { usePermissionsQuery } from '../api';

function PermissionsList() {
  const { data } = usePermissionsQuery({
    page: 1,
    page_size: 50,
  });

  return (
    <div>
      {data?.items.map((permission) => (
        <div key={permission.name}>
          <h3>{permission.name}</h3>
          <p>{permission.description}</p>
        </div>
      ))}
    </div>
  );
}
```

#### useCreatePermissionMutation & useDeletePermissionMutation

```typescript
import { 
  useCreatePermissionMutation, 
  useDeletePermissionMutation 
} from '../api';

function PermissionManagement() {
  const createPermission = useCreatePermissionMutation();
  const deletePermission = useDeletePermissionMutation();

  return (
    <div>
      <button 
        onClick={() => createPermission.mutate({
          name: 'custom:permission',
          description: 'Custom permission'
        })}
      >
        Create Permission
      </button>

      <button 
        onClick={() => deletePermission.mutate('custom:permission')}
      >
        Delete Permission
      </button>
    </div>
  );
}
```

---

## 🔐 Аутентификация

### useAuth Hook

```typescript
import { useAuth } from '../api';

function Component() {
  const { 
    user,           // Текущий пользователь или null
    isAuthenticated,// true если пользователь залогинен
    isLoading,      // true пока проверяем статус
    login,          // Функция для логина
    logout,         // Функция для логаута
    refreshUser,    // Обновить данные пользователя
  } = useAuth();

  return (
    <div>
      {isLoading && <p>Loading...</p>}
      {isAuthenticated ? (
        <div>
          <p>Welcome, {user?.username}!</p>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={() => login({ username: 'demo', password: 'demo' })}>
          Login
        </button>
      )}
    </div>
  );
}
```

### Protected Routes

```typescript
import { ProtectedRoute } from '../api';

// В routes.tsx
const routes = [
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <HomePage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/login',
    element: <LoginPage />, // Публичная страница
  },
];
```

---

## ❌ Обработка ошибок

### Типы ошибок

```typescript
import { ErrorCode } from '../api';

// Все возможные коды ошибок
ErrorCode.WRONG_LOGIN_DATA
ErrorCode.INVALID_TOKEN
ErrorCode.EXPIRED_TOKEN
ErrorCode.NOT_FOUND_USER
ErrorCode.PASSWORD_MISMATCH
ErrorCode.DUPLICATE_USER
ErrorCode.ACCESS_DENIED
// и другие...
```

### Type-safe обработка

```typescript
import { useLoginMutation, ErrorCode, ApiError } from '../api';
import { AxiosError } from 'axios';

function LoginForm() {
  const loginMutation = useLoginMutation({
    onError: (error: AxiosError<ApiError>) => {
      const errorCode = error.response?.data?.error?.code;
      const errorMessage = error.response?.data?.error?.message;
      const errorDetail = error.response?.data?.error?.detail;

      switch (errorCode) {
        case ErrorCode.WRONG_LOGIN_DATA:
          toast.error('Неверный логин или пароль');
          break;
        case ErrorCode.DUPLICATE_USER:
          toast.error(`Пользователь уже существует: ${errorDetail.field}`);
          break;
        default:
          toast.error(errorMessage || 'Произошла ошибка');
      }
    },
  });
}
```

### Глобальная обработка

```typescript
// В axiosInstance.ts уже есть обработка 400/EXPIRED_TOKEN
// Для дополнительной обработки:

import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    mutations: {
      onError: (error: AxiosError<ApiError>) => {
        // Логирование
        console.error('Mutation error:', error.response?.data);
        
        // Можно показать глобальный toast
        if (error.response?.data?.error?.code === ErrorCode.ACCESS_DENIED) {
          toast.error('У вас нет прав для этого действия');
        }
      },
    },
  },
});
```

---

## 💡 Примеры использования

### Пример 1: Login страница

```typescript
import { useState } from 'react';
import { useAuth } from '../api';

export function LoginPage() {
  const { login } = useAuth();
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await login(credentials);
      // Успех обрабатывается в AuthContext
    } catch (error) {
      // Ошибка обрабатывается в AuthContext
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={credentials.username}
        onChange={(e) => setCredentials(prev => ({ 
          ...prev, 
          username: e.target.value 
        }))}
        placeholder="Username"
      />
      <input
        type="password"
        value={credentials.password}
        onChange={(e) => setCredentials(prev => ({ 
          ...prev, 
          password: e.target.value 
        }))}
        placeholder="Password"
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

### Пример 2: Пагинация пользователей

```typescript
import { useState } from 'react';
import { useUsersQuery } from '../api';

export function UsersTable() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    is_active: true,
    page_size: 20,
  });

  const { data, isLoading, isFetching } = useUsersQuery({
    ...filters,
    page,
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Email</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data?.items.map((user) => (
            <tr key={user.id}>
              <td>{user.id}</td>
              <td>{user.username}</td>
              <td>{user.email}</td>
              <td>{user.is_active ? 'Active' : 'Inactive'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button 
          onClick={() => setPage(p => p - 1)} 
          disabled={page === 1 || isFetching}
        >
          Previous
        </button>
        <span>Page {page} of {data?.total_pages}</span>
        <button 
          onClick={() => setPage(p => p + 1)} 
          disabled={page === data?.total_pages || isFetching}
        >
          Next
        </button>
      </div>

      <div className="filters">
        <label>
          <input
            type="checkbox"
            checked={filters.is_active}
            onChange={(e) => setFilters(prev => ({
              ...prev,
              is_active: e.target.checked,
            }))}
          />
          Only active users
        </label>
      </div>
    </div>
  );
}
```

### Пример 3: Optimistic Updates

```typescript
import { useQueryClient, useMutation } from '@tanstack/react-query';
import { apiClient, userKeys } from '../api';

function ToggleUserStatus({ userId, isActive }) {
  const queryClient = useQueryClient();

  const toggleMutation = useMutation({
    mutationFn: async () => {
      // Предположим есть такой endpoint
      return apiClient.users.updateUser(userId, { is_active: !isActive });
    },
    // Optimistic update
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: userKeys.all });
      
      const previousData = queryClient.getQueryData(userKeys.list());
      
      queryClient.setQueryData(userKeys.list(), (old: any) => ({
        ...old,
        items: old.items.map((user: any) =>
          user.id === userId ? { ...user, is_active: !isActive } : user
        ),
      }));

      return { previousData };
    },
    onError: (err, variables, context) => {
      // Откатываем при ошибке
      if (context?.previousData) {
        queryClient.setQueryData(userKeys.list(), context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });

  return (
    <button onClick={() => toggleMutation.mutate()}>
      {isActive ? 'Deactivate' : 'Activate'}
    </button>
  );
}
```

### Пример 4: Параллельные запросы

```typescript
import { useQueries } from '@tanstack/react-query';
import { apiClient, userKeys, permissionKeys } from '../api';

function Dashboard() {
  const results = useQueries({
    queries: [
      {
        queryKey: userKeys.me(),
        queryFn: apiClient.users.getMe,
      },
      {
        queryKey: userKeys.sessions(),
        queryFn: apiClient.users.getSessions,
      },
      {
        queryKey: permissionKeys.list(),
        queryFn: () => apiClient.permissions.getPermissions(),
      },
    ],
  });

  const [meQuery, sessionsQuery, permissionsQuery] = results;

  if (results.some((q) => q.isLoading)) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Welcome, {meQuery.data?.username}</h1>
      <p>Active sessions: {sessionsQuery.data?.length}</p>
      <p>Permissions: {permissionsQuery.data?.items.length}</p>
    </div>
  );
}
```

---

## 🔄 Автоматический refresh

Refresh токена происходит **автоматически** когда:

1. Access token истекает (400/EXPIRED_TOKEN)
2. Axios interceptor ловит ошибку
3. Вызывает `POST /api/v1/auth/refresh` с `withCredentials: true`
4. Сервер читает refresh_token из HttpOnly cookie
5. Возвращает новый access_token
6. Повторяет исходный запрос

**Вам ничего делать не нужно!** Все работает прозрачно.

---

## 📝 Best Practices

1. **Всегда используйте hooks вместо прямых вызовов**
   ```typescript
   // ✅ Хорошо
   const { data } = useMeQuery();
   
   // ❌ Плохо (нет кеширования, refetch и т.д.)
   const data = await apiClient.users.getMe();
   ```

2. **Обрабатывайте ошибки локально**
   ```typescript
   const mutation = useLoginMutation({
     onError: (error) => {
       // Специфичная обработка для этого компонента
       toast.error(error.response?.data?.error?.message);
     },
   });
   ```

3. **Используйте Query Keys правильно**
   ```typescript
   // ✅ Используйте готовые key factories
   queryClient.invalidateQueries({ queryKey: userKeys.all });
   
   // ❌ Не хардкодите ключи
   queryClient.invalidateQueries({ queryKey: ['users'] });
   ```

4. **Не забывайте про cleanup**
   ```typescript
   useEffect(() => {
     return () => {
       queryClient.cancelQueries({ queryKey: userKeys.all });
     };
   }, []);
   ```

---

Больше примеров см. в [SECURITY.md](./SECURITY.md) и [API_INTEGRATION.md](./API_INTEGRATION.md)
