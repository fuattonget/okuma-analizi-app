import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add request interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
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
}

export interface AnalysisDetail {
  id: string;
  created_at: string;
  status: string;
  started_at?: string;
  finished_at?: string;
  error?: string;
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
  validation: {
    summary_consistent: boolean;
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
  async getAnalyses(limit: number = 20): Promise<AnalysisSummary[]> {
    const response = await api.get(`/v1/analyses/?limit=${limit}`);
    return response.data;
  },

  async getAnalysis(id: string): Promise<AnalysisDetail> {
    const response = await api.get(`/v1/analyses/${id}`);
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
};

export default api;
