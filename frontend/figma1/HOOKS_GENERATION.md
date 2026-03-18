# Генерация React Query Hooks из OpenAPI

## 🎯 Шаблон генерации

Этот документ показывает **как генерировать** React Query hooks из OpenAPI spec.

## 📝 Паттерны генерации

### GET endpoints → useQuery

```typescript
// OpenAPI:
// GET /api/v1/resource/{id}

// Generated Hook:
export const useResourceQuery = (
  id: string,
  options?: Omit<UseQueryOptions<ResourceResponse, AxiosError<ApiError>>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: resourceKeys.detail(id),
    queryFn: () => apiClient.resource.getResource(id),
    ...options,
  });
};
```

### POST endpoints → useMutation

```typescript
// OpenAPI:
// POST /api/v1/resource

// Generated Hook:
export const useCreateResourceMutation = (
  options?: UseMutationOptions<ResourceResponse, AxiosError<ApiError>, CreateResourceRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiClient.resource.createResource,
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: resourceKeys.all });
    },
    ...options,
  });
};
```

### PUT/PATCH endpoints → useMutation

```typescript
// OpenAPI:
// PUT /api/v1/resource/{id}

// Generated Hook:
export const useUpdateResourceMutation = (
  options?: UseMutationOptions<
    ResourceResponse, 
    AxiosError<ApiError>, 
    { id: string; data: UpdateResourceRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => apiClient.resource.updateResource(id, data),
    onSuccess: (_, variables) => {
      // Invalidate specific resource and list
      queryClient.invalidateQueries({ queryKey: resourceKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: resourceKeys.list() });
    },
    ...options,
  });
};
```

### DELETE endpoints → useMutation

```typescript
// OpenAPI:
// DELETE /api/v1/resource/{id}

// Generated Hook:
export const useDeleteResourceMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, string>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiClient.resource.deleteResource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: resourceKeys.all });
    },
    ...options,
  });
};
```

## 🔑 Query Keys Factory

Для каждого ресурса создайте key factory:

```typescript
export const resourceKeys = {
  // All keys for this resource
  all: ['resource'] as const,
  
  // List with filters
  lists: () => [...resourceKeys.all, 'list'] as const,
  list: (filters?: ResourceFilters) => 
    [...resourceKeys.lists(), filters] as const,
  
  // Detail
  details: () => [...resourceKeys.all, 'detail'] as const,
  detail: (id: string) => 
    [...resourceKeys.details(), id] as const,
  
  // Related data
  related: (id: string, relation: string) => 
    [...resourceKeys.detail(id), relation] as const,
};
```

## 🤖 Автоматическая генерация

### Используя openapi-typescript-codegen

```bash
npm install --save-dev openapi-typescript-codegen

npx openapi-typescript-codegen \
  --input ./openapi.json \
  --output ./src/api/generated \
  --client axios \
  --useOptions
```

### Используя orval

```bash
npm install --save-dev orval

# orval.config.ts
export default {
  petstore: {
    input: './openapi.json',
    output: {
      mode: 'tags-split',
      target: './src/api/generated',
      client: 'react-query',
      mock: true,
    },
  },
};

npx orval
```

## ✍️ Ручная генерация (наш подход)

### Шаг 1: Создайте types из schemas

```typescript
// From OpenAPI components/schemas
export interface UserResponse {
  id: number;
  email: string;
  username: string;
  // ...
}

export interface UserCreateRequest {
  email: string;
  username: string;
  password: string;
  repeat_password: string;
}
```

### Шаг 2: Создайте API client методы

```typescript
// src/api/client.ts
export const usersApi = {
  async getMe(): Promise<UserResponse> {
    const response = await axiosInstance.get<UserResponse>('/api/v1/users/me');
    return response.data;
  },

  async register(data: UserCreateRequest): Promise<UserResponse> {
    const response = await axiosInstance.post<UserResponse>(
      '/api/v1/users/register',
      data
    );
    return response.data;
  },

  // ...
};
```

### Шаг 3: Создайте query keys

```typescript
// src/api/hooks/useUsers.ts
export const userKeys = {
  all: ['users'] as const,
  me: () => [...userKeys.all, 'me'] as const,
  list: (params?: UserListParams) => [...userKeys.all, 'list', params] as const,
  sessions: () => [...userKeys.all, 'sessions'] as const,
};
```

### Шаг 4: Создайте hooks

```typescript
// Queries
export const useMeQuery = (options?) => {
  return useQuery({
    queryKey: userKeys.me(),
    queryFn: usersApi.getMe,
    ...options,
  });
};

// Mutations
export const useRegisterMutation = (options?) => {
  return useMutation({
    mutationFn: usersApi.register,
    ...options,
  });
};
```

## 📊 Mapping OpenAPI → Hooks

| OpenAPI | React Query | Hook Name |
|---------|-------------|-----------|
| `GET /users` | `useQuery` | `useUsersQuery` |
| `GET /users/{id}` | `useQuery` | `useUserQuery` |
| `POST /users` | `useMutation` | `useCreateUserMutation` |
| `PUT /users/{id}` | `useMutation` | `useUpdateUserMutation` |
| `DELETE /users/{id}` | `useMutation` | `useDeleteUserMutation` |
| `GET /users/me` | `useQuery` | `useMeQuery` |

## 🎨 Best Practices

### 1. Naming Convention

```typescript
// ✅ Good
useUsersQuery()        // List
useUserQuery()         // Single
useCreateUserMutation() // Create
useUpdateUserMutation() // Update
useDeleteUserMutation() // Delete

// ❌ Bad
getUsersHook()
createUser()
userMutation()
```

### 2. Options Type

```typescript
// ✅ Good - exclude queryKey and queryFn
type Options = Omit<
  UseQueryOptions<Data, Error>,
  'queryKey' | 'queryFn'
>;

// ❌ Bad - include everything
type Options = UseQueryOptions<Data, Error>;
```

### 3. Query Invalidation

```typescript
// ✅ Good - invalidate related queries
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: userKeys.all });
  queryClient.invalidateQueries({ queryKey: projectKeys.list() });
}

// ❌ Bad - manual refetch
onSuccess: () => {
  refetch();
}
```

### 4. Error Types

```typescript
// ✅ Good - use AxiosError<ApiError>
useMutation<Data, AxiosError<ApiError>, Variables>

// ❌ Bad - generic Error
useMutation<Data, Error, Variables>
```

## 🔧 Утилиты для генерации

### Скрипт для генерации hooks

```typescript
// scripts/generateHooks.ts
import fs from 'fs';
import { OpenAPIV3 } from 'openapi-types';

function generateHooks(spec: OpenAPIV3.Document) {
  const paths = spec.paths;
  
  Object.entries(paths).forEach(([path, pathItem]) => {
    Object.entries(pathItem).forEach(([method, operation]) => {
      if (method === 'get') {
        generateQueryHook(path, operation);
      } else {
        generateMutationHook(path, method, operation);
      }
    });
  });
}

function generateQueryHook(path: string, operation: any) {
  const hookName = `use${operationIdToHookName(operation.operationId)}Query`;
  
  return `
export const ${hookName} = (params?, options?) => {
  return useQuery({
    queryKey: queryKeys.${operation.operationId}(params),
    queryFn: () => apiClient.${operation.operationId}(params),
    ...options,
  });
};
  `.trim();
}

// ...
```

## 📚 Примеры из нашего проекта

### Auth Hooks

```typescript
// POST /api/v1/auth/login
export const useLoginMutation = (options?) => {
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      tokenManager.setAccessToken(data.access_token);
    },
    ...options,
  });
};

// POST /api/v1/auth/logout
export const useLogoutMutation = (options?) => {
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      tokenManager.clearAccessToken();
    },
    ...options,
  });
};
```

### User Hooks

```typescript
// GET /api/v1/users/me
export const useMeQuery = (options?) => {
  return useQuery({
    queryKey: userKeys.me(),
    queryFn: usersApi.getMe,
    ...options,
  });
};

// GET /api/v1/users/
export const useUsersQuery = (params?, options?) => {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => usersApi.getUsers(params),
    ...options,
  });
};

// POST /api/v1/users/register
export const useRegisterMutation = (options?) => {
  return useMutation({
    mutationFn: usersApi.register,
    ...options,
  });
};
```

## 🎯 Checklist для нового endpoint

Когда добавляете новый endpoint:

- [ ] Добавьте types из OpenAPI schema
- [ ] Создайте метод в API client
- [ ] Обновите query keys factory
- [ ] Создайте hook (useQuery или useMutation)
- [ ] Добавьте invalidation logic для mutations
- [ ] Добавьте type-safe error handling
- [ ] Экспортируйте из index.ts
- [ ] Добавьте пример использования в docs

## 🔗 Ссылки

- [TanStack Query](https://tanstack.com/query/latest)
- [OpenAPI Specification](https://swagger.io/specification/)
- [openapi-typescript-codegen](https://github.com/ferdikoomen/openapi-typescript-codegen)
- [orval](https://orval.dev/)
