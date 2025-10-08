import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add request interceptor to include JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    // Handle token expiration
    if (error.response?.status === 401) {
      // Clear stored auth data
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        // Redirect to login page
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);




// Types
export interface Text {
  id: string;
  text_id: string;
  title: string;
  grade: number;
  body: string;
  comment?: string;
  created_at: string;
  active: boolean;
}

export interface TextCreate {
  title: string;
  grade: number;
  body: string;
  comment?: string;
}

export interface TextUpdate {
  title: string;
  grade: number;
  body: string;
  comment?: string;
}


export interface AnalysisSummary {
  id: string;
  created_at: string;
  status: string;
  text_title: string;
  student_id?: string;
  wer?: number;
  accuracy?: number;
  wpm?: number;
  counts?: {
    correct: number;
    diff: number;
    missing: number;
    extra: number;
    substitution: number;
    repetition: number;
    total_words: number;
    total_pauses: number;
  };
  summary?: {
    counts?: {
      correct: number;
      missing: number;
      extra: number;
      substitution: number;
      repetition: number;
      total_words: number;
    };
    wer?: number;
    accuracy?: number;
    wpm?: number;
    long_pauses?: {
      count: number;
      threshold_ms: number;
    };
    error_types?: {
      missing: number;
      extra: number;
      substitution: number;
      repetition: number;
      pause_long: number;
    };
  };
  audio_id: string;
  // DEBUG fields
  timings?: {
    queued_at?: string;
    started_at?: string;
    finished_at?: string;
    total_ms?: number;
  };
  counts_direct?: {
    correct: number;
    missing: number;
    extra: number;
    diff: number;
  };
}

export interface AnalysisDetail {
  id: string;
  created_at: string;
  status: string;
  started_at?: string;
  finished_at?: string;
  error?: string;
  student_id?: string;
  summary: {
    counts?: {
      correct: number;
      missing: number;
      extra: number;
      substitution: number;
      repetition: number;
      total_words: number;
    };
    wer?: number;
    accuracy?: number;
    wpm?: number;
    long_pauses?: {
      count: number;
      threshold_ms: number;
    };
    error_types?: {
      missing: number;
      extra: number;
      substitution: number;
      repetition: number;
      pause_long: number;
    };
  };
  text: {
    title: string;
    body: string;
    grade: number;
  };
  // DEBUG fields
  timings?: {
    queued_at?: string;
    started_at?: string;
    finished_at?: string;
    total_ms?: number;
  };
  counts_direct?: {
    correct: number;
    missing: number;
    extra: number;
    diff: number;
  };
}

// Session types
export interface SessionSummary {
  id: string;
  text_id: string;
  audio_id: string;
  reader_id?: string;
  status: string;
  created_at: string;
  completed_at?: string;
}

export interface SessionDetail {
  id: string;
  text_id: string;
  audio_id: string;
  reader_id?: string;
  status: string;
  created_at: string;
  completed_at?: string;
  text: {
    title: string;
    body: string;
  };
  audio: {
    id: string;
    original_name: string;
    storage_name: string;
    content_type?: string;
    size_bytes?: number;
    duration_sec?: number;
    uploaded_at: string;
  };
}

// Event types
export interface WordEvent {
  id: string;
  analysis_id: string;
  position: number;
  ref_token?: string;
  hyp_token?: string;
  type: string;
  sub_type?: string;
  timing?: Record<string, number>;
  char_diff?: number;
  ref_idx?: number;
  hyp_idx?: number;
}

export interface PauseEvent {
  id: string;
  analysis_id: string;
  after_position: number;
  duration_ms: number;
  class_: string;
  start_ms: number;
  end_ms: number;
}

// Metrics type
export interface Metrics {
  analysis_id: string;
  counts: {
    correct: number;
    missing: number;
    extra: number;
    substitution: number;
    repetition: number;
    total_words: number;
  };
  wer: number;
  accuracy: number;
  wpm: number;
  long_pauses: {
    count: number;
    threshold_ms: number;
  };
  error_types: {
    missing: number;
    extra: number;
    substitution: number;
    repetition: number;
    pause_long: number;
  };
}

// Analysis Export type
export interface AnalysisExport {
  analysis_id: string;
  text_id: string;
  events: WordEvent[];
  pauses: PauseEvent[];
  summary: {
    counts: {
      correct: number;
      missing: number;
      extra: number;
      substitution: number;
      repetition: number;
      total_words: number;
    };
    wer: number;
    accuracy: number;
    wpm: number;
    long_pauses: {
      count: number;
      threshold_ms: number;
    };
    error_types: {
      missing: number;
      extra: number;
      substitution: number;
      repetition: number;
      pause_long: number;
    };
  };
  metrics: Record<string, any>;
  transcript?: string;
  validation: {
    summary_consistent: boolean;
  };
}

export interface UploadResponse {
  analysis_id: string;
}

// Auth interfaces
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    role: string;
    is_active: boolean;
    created_at: string;
  };
}

export interface User {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  role_permissions?: string[];
}

export interface Role {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  permissions?: string[];
  created_at: string;
}

// Student interfaces
export interface Student {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  grade: number;
  registration_number: number;
  created_by: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface StudentCreate {
  first_name: string;
  last_name: string;
  grade: number;
}

export interface StudentListResponse {
  students: Student[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// API functions
export const apiClient = {
  // Texts
  async getTexts(): Promise<Text[]> {
    const response = await api.get('/v1/texts');
    return response.data;
  },

  async createText(text: TextCreate): Promise<Text> {
    const response = await api.post('/v1/texts', text);
    return response.data;
  },


  async updateText(id: string, text: TextUpdate): Promise<Text> {
    const response = await api.put(`/v1/texts/${id}`, text);
    return response.data;
  },

  async deleteText(id: string): Promise<void> {
    await api.delete(`/v1/texts/${id}`);
  },

  // Upload
  async uploadAudio(file: File, textId: string, studentId?: string): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('text_id', textId);
    if (studentId) {
      formData.append('student_id', studentId);
    }

    const response = await api.post('/v1/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Audio URL
  async getAnalysisAudioUrl(analysisId: string, expirationHours: number = 1): Promise<{
    analysis_id: string;
    audio_id: string;
    signed_url: string;
    expiration_hours: number;
    expires_at: string;
  }> {
    const response = await api.get(`/v1/analyses/${analysisId}/audio-url`, {
      params: { expiration_hours: expirationHours }
    });
    return response.data;
  },

  // Analyses
  async getAnalyses(limit: number = 20, studentId?: string): Promise<AnalysisSummary[]> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (studentId) {
      params.append('student_id', studentId);
    }
    const response = await api.get(`/v1/analyses/?${params.toString()}`);
    return response.data;
  },

  async getAnalysis(id: string): Promise<AnalysisDetail> {
    const response = await api.get(`/v1/analyses/${id}`);
    return response.data;
  },


  // Sessions
  async getSessions(limit: number = 20, status?: string, reader_id?: string): Promise<SessionSummary[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (status) params.append('status', status);
    if (reader_id) params.append('reader_id', reader_id);
    
    const response = await api.get(`/v1/sessions?${params.toString()}`);
    return response.data;
  },

  async getSession(sessionId: string): Promise<SessionDetail> {
    const response = await api.get(`/v1/sessions/${sessionId}`);
    return response.data;
  },

  async getSessionAnalyses(sessionId: string, limit: number = 20): Promise<AnalysisSummary[]> {
    const response = await api.get(`/v1/sessions/${sessionId}/analyses?limit=${limit}`);
    return response.data;
  },

  async updateSessionStatus(sessionId: string, status: string): Promise<{ message: string; session_id: string }> {
    const response = await api.put(`/v1/sessions/${sessionId}/status?status=${status}`);
    return response.data;
  },

  // Analysis Events
  async getWordEvents(analysisId: string): Promise<WordEvent[]> {
    const response = await api.get(`/v1/analyses/${analysisId}/word-events`);
    return response.data;
  },

  async getPauseEvents(analysisId: string): Promise<PauseEvent[]> {
    const response = await api.get(`/v1/analyses/${analysisId}/pause-events`);
    return response.data;
  },

  async getMetrics(analysisId: string): Promise<Metrics> {
    const response = await api.get(`/v1/analyses/${analysisId}/metrics`);
    return response.data;
  },

  // Analysis Export
  async getAnalysisExport(id: string): Promise<AnalysisExport> {
    const response = await api.get(`/v1/analyses/${id}/export`);
    return response.data;
  },

  // Auth
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await api.post('/v1/auth/login', { email, password });
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/v1/auth/me');
    return response.data;
  },

  async logout(): Promise<void> {
    await api.post('/v1/auth/logout');
  },

  // User management
  async getUsers(page: number = 1, pageSize: number = 20, search?: string, role?: string): Promise<{
    users: User[];
    total: number;
    page: number;
    page_size: number;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (search) params.append('search', search);
    if (role) params.append('role', role);
    
    const response = await api.get(`/v1/users?${params.toString()}`);
    return response.data;
  },

  async getUser(userId: string): Promise<User> {
    const response = await api.get(`/v1/users/${userId}`);
    return response.data;
  },

  async createUser(userData: {
    email: string;
    username: string;
    password: string;
    role: string;
    is_active?: boolean;
  }): Promise<User> {
    const response = await api.post('/v1/users', userData);
    return response.data;
  },

  async updateUser(userId: string, userData: {
    email?: string;
    username?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<User> {
    const response = await api.put(`/v1/users/${userId}`, userData);
    return response.data;
  },

  async deleteUser(userId: string): Promise<void> {
    await api.delete(`/v1/users/${userId}`);
  },

  async resetUserPassword(userId: string, newPassword: string): Promise<{
    message: string;
    new_password: string;
    user_email: string;
    user_username: string;
  }> {
    const response = await api.post(`/v1/users/${userId}/reset-password`, { new_password: newPassword });
    return response.data;
  },

  async getAvailableRoles(): Promise<string[]> {
    const response = await api.get('/v1/users/roles/available');
    return response.data;
  },

  // Students
  async getStudents(
    page: number = 1, 
    pageSize: number = 20, 
    grade?: number | string, 
    search?: string, 
    isActive?: boolean,
    createdAfter?: string,
    createdBefore?: string,
    sortBy?: string,
    sortOrder?: string
  ): Promise<StudentListResponse> {
    console.log('🔍 API: getStudents called with params:', { 
      page, pageSize, grade, search, isActive, createdAfter, createdBefore, sortBy, sortOrder 
    });
    
    const params: any = { page, page_size: pageSize };
    if (grade) params.grade = grade;
    if (search) params.search = search;
    if (isActive !== undefined) params.is_active = isActive;
    if (createdAfter) params.created_after = createdAfter;
    if (createdBefore) params.created_before = createdBefore;
    if (sortBy) params.sort_by = sortBy;
    if (sortOrder) params.sort_order = sortOrder;
    
    console.log('🔍 API: Final params:', params);
    
    try {
      const response = await api.get('/v1/students', { params });
      console.log('🔍 API: getStudents response:', response.data);
      return response.data;
    } catch (error) {
      console.error('🔍 API: getStudents error:', error);
      throw error;
    }
  },

  async createStudent(student: StudentCreate): Promise<Student> {
    const response = await api.post('/v1/students', student);
    return response.data;
  },

  async getStudent(id: string): Promise<Student> {
    const response = await api.get(`/v1/students/${id}`);
    return response.data;
  },

  async updateStudent(id: string, student: Partial<StudentCreate & { is_active?: boolean }>): Promise<Student> {
    const response = await api.put(`/v1/students/${id}`, student);
    return response.data;
  },

  async deleteStudent(id: string): Promise<void> {
    await api.delete(`/v1/students/${id}`);
  },

  // Role management
  async getRoles(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: 'all' | 'active' | 'inactive';
  }): Promise<{
    roles: Role[];
    total: number;
    page: number;
    page_size: number;
  }> {
    const response = await api.get('/v1/roles', { params });
    return response.data;
  },

  async getRole(roleId: string): Promise<Role> {
    const response = await api.get(`/v1/roles/${roleId}`);
    return response.data;
  },

  async createRole(roleData: {
    name: string;
    display_name: string;
    description?: string;
    permissions: string[];
  }): Promise<Role> {
    const response = await api.post('/v1/roles', roleData);
    return response.data;
  },

  async updateRole(roleId: string, roleData: {
    display_name?: string;
    description?: string;
    permissions?: string[];
    is_active?: boolean;
  }): Promise<Role> {
    const response = await api.put(`/v1/roles/${roleId}`, roleData);
    return response.data;
  },

  async deleteRole(roleId: string): Promise<void> {
    await api.delete(`/v1/roles/${roleId}`);
  },

  async getAvailablePermissions(): Promise<string[]> {
    const response = await api.get('/v1/roles/permissions/available');
    return response.data;
  },

  async getPermissionsGrouped(): Promise<Record<string, string[]>> {
    const response = await api.get('/v1/roles/permissions/grouped');
    return response.data;
  },

  // Profile Management
  async getMyProfile(): Promise<{
    id: string;
    email: string;
    username: string;
    role_name: string;
    role_display_name: string;
    created_at: string;
    updated_at: string;
  }> {
    const response = await api.get('/v1/profile/me');
    return response.data;
  },

  async updateMyProfile(profileData: {
    username?: string;
    email?: string;
  }): Promise<{
    id: string;
    email: string;
    username: string;
    role_name: string;
    role_display_name: string;
    created_at: string;
    updated_at: string;
  }> {
    const response = await api.put('/v1/profile/me', profileData);
    return response.data;
  },

  async changeMyPassword(passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<{
    message: string;
    success: boolean;
  }> {
    const response = await api.post('/v1/profile/me/change-password', passwordData);
    return response.data;
  },
};

export default api;
