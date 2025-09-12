import { create } from 'zustand';

interface AnalysisStore {
  analyses: any[];
  pollingIntervals: Map<string, NodeJS.Timeout>;
  setAnalyses: (analyses: any[]) => void;
  addAnalysis: (analysis: any) => void;
  updateAnalysis: (id: string, updates: Partial<any>) => void;
  startPolling: (id: string, callback: () => Promise<void>) => void;
  stopPolling: (id: string) => void;
  stopAllPolling: () => void;
}

export const useAnalysisStore = create<AnalysisStore>((set, get) => ({
  analyses: [],
  pollingIntervals: new Map(),
  
  setAnalyses: (analyses) => set({ analyses }),
  
  addAnalysis: (analysis) => set((state) => ({ 
    analyses: [analysis, ...state.analyses] 
  })),
  
  updateAnalysis: (id, updates) => set((state) => ({
    analyses: state.analyses.map(analysis => 
      analysis.id === id ? { ...analysis, ...updates } : analysis
    )
  })),
  
  startPolling: (id, callback) => {
    const { pollingIntervals } = get();
    
    // Stop existing polling for this ID
    if (pollingIntervals.has(id)) {
      clearInterval(pollingIntervals.get(id)!);
    }
    
    // Start new polling
    const interval = setInterval(async () => {
      try {
        await callback();
      } catch (error) {
        console.error(`Polling error for analysis ${id}:`, error);
      }
    }, 1000);
    
    set((state) => ({
      pollingIntervals: new Map(state.pollingIntervals).set(id, interval)
    }));
  },
  
  stopPolling: (id) => {
    const { pollingIntervals } = get();
    const interval = pollingIntervals.get(id);
    
    if (interval) {
      clearInterval(interval);
      set((state) => {
        const newIntervals = new Map(state.pollingIntervals);
        newIntervals.delete(id);
        return { pollingIntervals: newIntervals };
      });
    }
  },
  
  stopAllPolling: () => {
    const { pollingIntervals } = get();
    
    pollingIntervals.forEach((interval) => {
      clearInterval(interval);
    });
    
    set({ pollingIntervals: new Map() });
  },
}));
