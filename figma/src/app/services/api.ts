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

export interface ProfileDTO {
  id: number;
  avatars?: Record<string, string>;
  specialization?: string;
  display_name?: string;
  bio?: string;
  date_birthday?: string;
  skills: string[];
  contacts: Array<{ provider: string; contact: string }>;
}

export interface ProjectDTO {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description?: string;
  full_description?: string;
  visibility: 'public' | 'private';
  tags: string[];
  meta_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
  memberships?: Array<any>;
}

export interface PositionDTO {
  id: string;
  project_id: number;
  title: string;
  description?: string;
  responsibilities?: string;
  required_skills: string[];
  is_open: boolean;
  location_type: 'remote' | 'onsite' | 'hybrid';
  expected_load: 'low' | 'medium' | 'high';
  created_at?: string;
  updated_at?: string;
}

export interface ApplicationDTO {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  message?: string;
  decided_by?: number;
  decided_at?: string;
  created_at?: string;
  updated_at?: string;
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
    password_repeat: string;
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

// Profiles API
export const profilesApi = {
  async createProfile(data: {
    display_name?: string;
    bio?: string;
    skills?: string[];
    date_birthday?: string;
  }): Promise<ProfileDTO> {
    return apiRequest<ProfileDTO>('/api/v1/profiles/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getProfiles(params?: {
    display_name?: string;
    skills?: string[];
    page?: number;
    page_size?: number;
  }): Promise<PageResult<ProfileDTO>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, String(v)));
          } else {
            queryParams.append(key, String(value));
          }
        }
      });
    }

    return apiRequest<PageResult<ProfileDTO>>(
      `/api/v1/profiles/${params ? '?' + queryParams.toString() : ''}`
    );
  },

  async getProfile(id: number): Promise<ProfileDTO> {
    return apiRequest<ProfileDTO>(`/api/v1/profiles/${id}`);
  },

  async updateProfile(id: number, data: {
    specialization?: string;
    display_name?: string;
    bio?: string;
    skills?: string[];
    date_birthday?: string;
  }): Promise<ProfileDTO> {
    return apiRequest<ProfileDTO>(`/api/v1/profiles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async addContact(id: number, data: {
    provider: string;
    contact: string;
  }): Promise<void> {
    return apiRequest<void>(`/api/v1/profiles/${id}/contacts`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async deleteContact(id: number, provider: string): Promise<void> {
    return apiRequest<void>(`/api/v1/profiles/${id}/${provider}/delete`, {
      method: 'DELETE',
    });
  },
};

// Projects API
export const projectsApi = {
  async getProjects(params?: {
    name?: string;
    slug?: string;
    tags?: string[];
    page?: number;
    page_size?: number;
    sort?: string;
  }): Promise<PageResult<ProjectDTO>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, String(v)));
          } else {
            queryParams.append(key, String(value));
          }
        }
      });
    }

    return apiRequest<PageResult<ProjectDTO>>(
      `/api/v1/projects/${params ? '?' + queryParams.toString() : ''}`
    );
  },

  async getMyProjects(params?: {
    page?: number;
    page_size?: number;
  }): Promise<PageResult<ProjectDTO>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }

    return apiRequest<PageResult<ProjectDTO>>(
      `/api/v1/projects/my${params ? '?' + queryParams.toString() : ''}`
    );
  },

  async getProject(id: number): Promise<ProjectDTO> {
    return apiRequest<ProjectDTO>(`/api/v1/projects/${id}`);
  },

  async createProject(data: {
    name: string;
    slug: string;
    small_description?: string;
    description?: string;
    visibility: 'public' | 'private';
    tags?: string[];
    meta_data?: Record<string, any>;
  }): Promise<ProjectDTO> {
    return apiRequest<ProjectDTO>('/api/v1/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateProject(id: number, data: Partial<ProjectDTO>): Promise<ProjectDTO> {
    return apiRequest<ProjectDTO>(`/api/v1/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deleteProject(id: number): Promise<void> {
    return apiRequest<void>(`/api/v1/projects/${id}`, {
      method: 'DELETE',
    });
  },

  async getProjectPositions(id: number): Promise<PositionDTO[]> {
    return apiRequest<PositionDTO[]>(`/api/v1/projects/${id}/positions`);
  },

  async createProjectPosition(id: number, data: {
    title: string;
    description?: string;
    responsibilities?: string;
    required_skills?: string[];
    is_open?: boolean;
    location_type?: 'remote' | 'onsite' | 'hybrid';
    expected_load?: 'low' | 'medium' | 'high';
  }): Promise<PositionDTO> {
    return apiRequest<PositionDTO>(`/api/v1/projects/${id}/positions`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// Positions API
export const positionsApi = {
  async getPositions(params?: {
    project_id?: number;
    title?: string;
    required_skills?: string[];
    is_open?: boolean;
    location_type?: 'remote' | 'onsite' | 'hybrid';
    expected_load?: 'low' | 'medium' | 'high';
    page?: number;
    page_size?: number;
  }): Promise<PageResult<PositionDTO>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, String(v)));
          } else {
            queryParams.append(key, String(value));
          }
        }
      });
    }

    return apiRequest<PageResult<PositionDTO>>(
      `/api/v1/positions/${params ? '?' + queryParams.toString() : ''}`
    );
  },

  async getPosition(uuid: string): Promise<PositionDTO> {
    return apiRequest<PositionDTO>(`/api/v1/positions/${uuid}`);
  },

  async updatePosition(uuid: string, data: Partial<PositionDTO>): Promise<PositionDTO> {
    return apiRequest<PositionDTO>(`/api/v1/positions/${uuid}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deletePosition(uuid: string): Promise<void> {
    return apiRequest<void>(`/api/v1/positions/${uuid}`, {
      method: 'DELETE',
    });
  },

  async getPositionApplications(uuid: string): Promise<ApplicationDTO[]> {
    return apiRequest<ApplicationDTO[]>(`/api/v1/positions/${uuid}/applications`);
  },

  async createApplication(uuid: string, data?: { message?: string }): Promise<ApplicationDTO> {
    return apiRequest<ApplicationDTO>(`/api/v1/positions/${uuid}/applications`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });
  },
};

// Applications API
export const applicationsApi = {
  async getApplications(params?: {
    project_id?: number;
    position_id?: string;
    candidate_id?: number;
    status?: 'pending' | 'accepted' | 'rejected';
    page?: number;
    page_size?: number;
  }): Promise<PageResult<ApplicationDTO>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }

    return apiRequest<PageResult<ApplicationDTO>>(
      `/api/v1/applications/${params ? '?' + queryParams.toString() : ''}`
    );
  },

  async getMyApplications(params?: {
    page?: number;
    page_size?: number;
  }): Promise<PageResult<ApplicationDTO>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }

    return apiRequest<PageResult<ApplicationDTO>>(
      `/api/v1/applications/me${params ? '?' + queryParams.toString() : ''}`
    );
  },

  async approveApplication(uuid: string): Promise<ApplicationDTO> {
    return apiRequest<ApplicationDTO>(`/api/v1/applications/${uuid}/approve`, {
      method: 'POST',
    });
  },

  async rejectApplication(uuid: string): Promise<ApplicationDTO> {
    return apiRequest<ApplicationDTO>(`/api/v1/applications/${uuid}/reject`, {
      method: 'POST',
    });
  },
};