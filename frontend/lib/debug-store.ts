import { create } from 'zustand';

interface DebugInfo {
  debug: boolean;
  log_level: string;
  log_format: string;
  long_pause_ms: number;
  mongo_db: string;
  redis_ok: boolean;
  uptime_s: number;
}

interface ApiCall {
  method: string;
  url: string;
  status?: number;
  duration_ms?: number;
  timestamp: number;
  request_id?: string;
}

interface DebugStore {
  visible: boolean;
  debugInfo: DebugInfo | null;
  apiCalls: ApiCall[];
  loading: boolean;
  error: string | null;
  
  // Actions
  toggle: () => void;
  setVisible: (visible: boolean) => void;
  setDebugInfo: (info: DebugInfo) => void;
  addApiCall: (call: ApiCall) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearApiCalls: () => void;
}

export const useDebugStore = create<DebugStore>((set, get) => ({
  visible: false,
  debugInfo: null,
  apiCalls: [],
  loading: false,
  error: null,
  
  toggle: () => set((state) => ({ visible: !state.visible })),
  setVisible: (visible) => set({ visible }),
  setDebugInfo: (debugInfo) => set({ debugInfo }),
  addApiCall: (call) => set((state) => ({ 
    apiCalls: [...state.apiCalls.slice(-49), call] // Keep last 50 calls
  })),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearApiCalls: () => set({ apiCalls: [] }),
}));

// Keyboard shortcut handler
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'd') {
      e.preventDefault();
      useDebugStore.getState().toggle();
    }
  });
}


