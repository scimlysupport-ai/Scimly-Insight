import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthUser } from "../services/authService";

// Phase 12 — Authentication.
// Holds the JWT + logged-in user's profile. Persisted to localStorage
// so refreshing the page (or closing/reopening the tab) doesn't log
// anyone out. apiClient.ts reads the token from here to attach
// Authorization: Bearer on every request once someone's logged in.
interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isLoggedIn: () => boolean;
  logIn: (token: string, user: AuthUser) => void;
  logOut: () => void;
  setUser: (user: AuthUser) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoggedIn: () => !!get().token,
      logIn: (token, user) => set({ token, user }),
      logOut: () => set({ token: null, user: null }),
      setUser: (user) => set({ user }),
    }),
    { name: "scimly_auth" }
  )
);
