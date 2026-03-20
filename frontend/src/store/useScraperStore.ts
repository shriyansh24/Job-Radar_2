import { create } from 'zustand';

export interface ScraperEvent {
  type: string;
  data: string;
  timestamp: string;
}

interface ScraperState {
  isRunning: boolean;
  events: ScraperEvent[];
  setRunning: (v: boolean) => void;
  addEvent: (e: ScraperEvent) => void;
  clearEvents: () => void;
}

export const useScraperStore = create<ScraperState>((set) => ({
  isRunning: false,
  events: [],
  setRunning: (v) => set({ isRunning: v }),
  addEvent: (e) => set((state) => ({ events: [...state.events, e] })),
  clearEvents: () => set({ events: [] }),
}));
