// API клиент для взаимодействия с бэкендом
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Типы для API responses
export interface ApiError {
  error: {
    code: string;
    message: string;
    detail: Record<string, any>;
  };
  status: number;
  request_id: string;
  timestamp: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Функция для получения access token из localStorage
function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

// Функция для сохранения access token
export function setAccessToken(token: string) {
  localStorage.setItem('access_token', token);
}

// Функция для удаления access token
export function clearAccessToken() {
  localStorage.removeItem('access_token');
}

// Базовая функция для API запросов
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Для работы с cookies (refresh token)
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw error;
  }

  // Для 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Auth API
export const authApi = {
  async login(username: string, password: string): Promise<AccessTokenResponse> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    return apiRequest<AccessTokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
  },

  async register(data: {
    email: string;
    username: string;
    password: string;
    repeat_password: string;
  }): Promise<UserResponse> {
    return apiRequest<UserResponse>('/api/v1/users/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async logout(): Promise<void> {
    return apiRequest<void>('/api/v1/auth/logout', {
      method: 'POST',
    });
  },

  async refreshToken(): Promise<AccessTokenResponse> {
    return apiRequest<AccessTokenResponse>('/api/v1/auth/refresh', {
      method: 'POST',
    });
  },
};

// Users API
export const usersApi = {
  async getMe(): Promise<UserResponse> {
    return apiRequest<UserResponse>('/api/v1/users/me');
  },

  async getUsers(params: {
    email?: string;
    username?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
    sort?: string;
  }): Promise<PageResult<UserResponse>> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, String(value));
      }
    });

    return apiRequest<PageResult<UserResponse>>(
      `/api/v1/users/?${queryParams.toString()}`
    );
  },
};

// Projects API (будущие endpoints)
export const projectsApi = {
  // TODO: Реализовать когда будут доступны endpoints
  async getProjects(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    skills?: string[];
    status?: string;
  }): Promise<any> {
    // Mock implementation
    throw new Error('Projects API не реализован');
  },

  async getProject(id: string): Promise<any> {
    throw new Error('Projects API не реализован');
  },

  async createProject(data: any): Promise<any> {
    throw new Error('Projects API не реализован');
  },

  async updateProject(id: string, data: any): Promise<any> {
    throw new Error('Projects API не реализован');
  },

  async deleteProject(id: string): Promise<void> {
    throw new Error('Projects API не реализован');
  },
};

// Positions API (будущие endpoints)
export const positionsApi = {
  async getPositions(projectId: string): Promise<any> {
    throw new Error('Positions API не реализован');
  },

  async createPosition(projectId: string, data: any): Promise<any> {
    throw new Error('Positions API не реализован');
  },

  async deletePosition(positionId: string): Promise<void> {
    throw new Error('Positions API не реализован');
  },
};

// Applications API (будущие endpoints)
export const applicationsApi = {
  async getMyApplications(): Promise<any> {
    throw new Error('Applications API не реализован');
  },

  async createApplication(positionId: string, data: any): Promise<any> {
    throw new Error('Applications API не реализован');
  },

  async getApplicationsForProject(projectId: string): Promise<any> {
    throw new Error('Applications API не реализован');
  },

  async updateApplicationStatus(
    applicationId: string,
    status: 'accepted' | 'rejected'
  ): Promise<any> {
    throw new Error('Applications API не реализован');
  },
};

// Skills API (будущие endpoints)
export const skillsApi = {
  async getSkills(): Promise<any> {
    throw new Error('Skills API не реализован');
  },

  async getUserSkills(userId: number): Promise<any> {
    throw new Error('Skills API не реализован');
  },

  async updateUserSkills(skills: string[]): Promise<any> {
    throw new Error('Skills API не реализован');
  },
};
