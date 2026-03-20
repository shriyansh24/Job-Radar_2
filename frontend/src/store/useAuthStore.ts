import { create } from "zustand";
import { getMeApi, loginApi } from "../api/auth";
import type { User } from "../lib/types";

function getStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  const s = window.localStorage;
  if (!s) return null;
  if (typeof s.getItem !== "function") return null;
  if (typeof s.setItem !== "function") return null;
  if (typeof s.removeItem !== "function") return null;
  return s;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  loadFromStorage: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: getStorage()?.getItem("access_token") ?? null,
  isAuthenticated: !!getStorage()?.getItem("access_token"),

  login: async (email: string, password: string) => {
    const data = await loginApi(email, password);
    const storage = getStorage();
    storage?.setItem("access_token", data.access_token);
    storage?.setItem("refresh_token", data.refresh_token);
    const user = await getMeApi();
    set({ user, token: data.access_token, isAuthenticated: true });
  },

  logout: () => {
    const storage = getStorage();
    storage?.removeItem("access_token");
    storage?.removeItem("refresh_token");
    set({ user: null, token: null, isAuthenticated: false });
  },

  refresh: async () => {
    try {
      const user = await getMeApi();
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, token: null, isAuthenticated: false });
      const storage = getStorage();
      storage?.removeItem("access_token");
      storage?.removeItem("refresh_token");
    }
  },

  loadFromStorage: async () => {
    const storage = getStorage();
    const token = storage?.getItem("access_token");
    if (!token) {
      set({ isAuthenticated: false });
      return;
    }
    try {
      const user = await getMeApi();
      set({ user, token, isAuthenticated: true });
    } catch {
      storage?.removeItem("access_token");
      storage?.removeItem("refresh_token");
      set({ user: null, token: null, isAuthenticated: false });
    }
  },
}));
