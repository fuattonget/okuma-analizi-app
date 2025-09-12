import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const DEBUG_MODE = process.env.NEXT_PUBLIC_DEBUG === '1';
const LOG_API = process.env.NEXT_PUBLIC_LOG_API === '1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API call history for debug panel
let apiCallHistory: Array<{
  method: string;
  url: string;
  status?: number;
  duration_ms?: number;
  timestamp: number;
  request_id?: string;
}> = [];

// Request interceptor for DEBUG logging
api.interceptors.request.use(
  (config) => {
    if (LOG_API) {
      (config as any).startedAt = performance.now();
      console.debug('[API] Request started:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        baseURL: config.baseURL
      });
    }
    return config;
  },
  (error) => {
    if (LOG_API) {
      console.error('[API-ERR] Request error:', error);
    }
    return Promise.reject(error);
  }
);

// Response interceptor for DEBUG logging
api.interceptors.response.use(
  (response) => {
    if (LOG_API) {
      const duration_ms = (performance.now() - (response.config as any).startedAt).toFixed(2);
      const request_id = response.headers['x-request-id'];
      
      const callInfo = {
        method: response.config.method?.toUpperCase() || 'UNKNOWN',
        url: response.config.url || '',
        status: response.status,
        duration_ms: parseFloat(duration_ms),
        timestamp: Date.now(),
        request_id: request_id
      };
      
      apiCallHistory.push(callInfo);
      
      // Keep only last 50 calls
      if (apiCallHistory.length > 50) {
        apiCallHistory = apiCallHistory.slice(-50);
      }
      
      console.debug('[API] Response received:', callInfo);
      
      if (request_id) {
        console.debug(`[API] Request ID: ${request_id}`);
      }
    }
    return response;
  },
  (error) => {
    if (LOG_API) {
      const duration_ms = error.config ? 
        (performance.now() - (error.config as any).startedAt).toFixed(2) : 'N/A';
      
      const callInfo = {
        method: error.config?.method?.toUpperCase() || 'UNKNOWN',
        url: error.config?.url || '',
        status: error.response?.status || 0,
        duration_ms: duration_ms === 'N/A' ? 0 : parseFloat(duration_ms),
        timestamp: Date.now(),
        request_id: error.response?.headers?.['x-request-id']
      };
      
      apiCallHistory.push(callInfo);
      console.error('[API-ERR] Response error:', callInfo);
    }
    return Promise.reject(error);
  }
);

// Export API call history for debug panel
export const getApiCallHistory = () => apiCallHistory;

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
  wer?: number;
  accuracy?: number;
  wpm?: number;
  counts?: {
    correct: number;
    diff: number;
    missing: number;
    extra: number;
    total_words: number;
    total_pauses: number;
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
  summary: Record<string, any>;
  text: {
    title: string;
    body: string;
  };
  audio_url: string;
  word_events: Array<{
    idx: number;
    ref_token?: string;
    hyp_token?: string;
    start_ms?: number;
    end_ms?: number;
    type: string;
    subtype?: string;
    details: Record<string, any>;
  }>;
  pause_events: Array<{
    after_word_idx: number;
    start_ms: number;
    end_ms: number;
    duration_ms: number;
  }>;
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

export interface UploadResponse {
  analysis_id: string;
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
  async uploadAudio(file: File, textId: string): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('text_id', textId);

    const response = await api.post('/v1/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Analyses
  async getAnalyses(limit: number = 20): Promise<AnalysisSummary[]> {
    const response = await api.get(`/v1/analyses?limit=${limit}`);
    return response.data;
  },

  async getAnalysis(id: string): Promise<AnalysisDetail> {
    const response = await api.get(`/v1/analyses/${id}`);
    return response.data;
  },

  async getAnalysisStatus(id: string): Promise<{ status: string }> {
    const response = await api.get(`/v1/upload/status/${id}`);
    return response.data;
  },
};

export default api;
