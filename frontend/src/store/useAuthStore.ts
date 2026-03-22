import { create } from "zustand";
import { getMeApi, loginApi, logoutApi, refreshApi } from "../api/auth";
import type { User } from "../lib/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  initialized: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  loadFromSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  initialized: false,

  login: async (email: string, password: string) => {
    await loginApi(email, password);
    const user = await getMeApi();
    set({ user, isAuthenticated: true, initialized: true });
  },

  logout: async () => {
    try {
      await logoutApi();
    } finally {
      set({ user: null, isAuthenticated: false, initialized: true });
    }
  },

  refresh: async () => {
    try {
      await refreshApi();
      const user = await getMeApi();
      set({ user, isAuthenticated: true, initialized: true });
    } catch {
      set({ user: null, isAuthenticated: false, initialized: true });
    }
  },

  loadFromSession: async () => {
    try {
      const user = await getMeApi();
      set({ user, isAuthenticated: true, initialized: true });
    } catch {
      try {
        await refreshApi();
        const user = await getMeApi();
        set({ user, isAuthenticated: true, initialized: true });
      } catch {
        set({ user: null, isAuthenticated: false, initialized: true });
      }
    }
  },
}));
