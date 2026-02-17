/**
 * Authentication state management using Zustand.
 */

import { create } from "zustand";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  is_premium_user: boolean;
  credits_used: number;
  credits_limit: number;
  remaining_credits: number | null;
  created_at: string;
}

interface AuthStore {
  // State
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;

  // Computed
  isAuthenticated: () => boolean;

  // Actions
  setUser: (user: AuthUser | null) => void;
  setToken: (token: string | null) => void;
  setError: (error: string | null) => void;

  signup: (email: string, password: string, name: string) => Promise<boolean>;
  signin: (email: string, password: string) => Promise<boolean>;
  signout: () => void;
  fetchMe: () => Promise<void>;
  refreshUser: () => Promise<void>;

  // Initialize from localStorage
  initialize: () => void;
}

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("metagpt-token");
  } catch {
    return null;
  }
}

function storeToken(token: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (token) {
      localStorage.setItem("metagpt-token", token);
    } else {
      localStorage.removeItem("metagpt-token");
    }
  } catch {}
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  token: getStoredToken(),
  isLoading: false,
  error: null,

  isAuthenticated: () => {
    return !!get().token && !!get().user;
  },

  setUser: (user) => set({ user }),
  setToken: (token) => {
    storeToken(token);
    set({ token });
  },
  setError: (error) => set({ error }),

  signup: async (email: string, password: string, name: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        set({
          error: data.detail || "Signup failed",
          isLoading: false,
        });
        return false;
      }

      const data = await res.json();
      storeToken(data.token);
      set({
        token: data.token,
        user: data.user,
        isLoading: false,
        error: null,
      });
      return true;
    } catch {
      set({ error: "Network error. Please try again.", isLoading: false });
      return false;
    }
  },

  signin: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/signin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        set({
          error: data.detail || "Invalid email or password",
          isLoading: false,
        });
        return false;
      }

      const data = await res.json();
      storeToken(data.token);
      set({
        token: data.token,
        user: data.user,
        isLoading: false,
        error: null,
      });
      return true;
    } catch {
      set({ error: "Network error. Please try again.", isLoading: false });
      return false;
    }
  },

  signout: () => {
    storeToken(null);
    set({ token: null, user: null, error: null });
  },

  fetchMe: async () => {
    const token = get().token;
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        // Token expired or invalid
        storeToken(null);
        set({ token: null, user: null });
        return;
      }

      const user = await res.json();
      set({ user });
    } catch {
      // Network error — keep token but clear user
    }
  },

  refreshUser: async () => {
    await get().fetchMe();
  },

  initialize: () => {
    const token = getStoredToken();
    if (token) {
      set({ token });
      get().fetchMe();
    }
  },
}));
