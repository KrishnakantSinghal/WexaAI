import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Organization } from "@/types";

interface AuthState {
  accessToken: string | null;
  user: User | null;
  organization: Organization | null;
  isAuthenticated: boolean;
  hasHydrated: boolean;
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  setOrganization: (org: Organization) => void;
  setHasHydrated: (v: boolean) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      organization: null,
      isAuthenticated: false,
      hasHydrated: false,

      setAccessToken: (token) =>
        set({ accessToken: token, isAuthenticated: true }),

      setUser: (user) => set({ user }),

      setOrganization: (org) => set({ organization: org }),

      setHasHydrated: (v) => set({ hasHydrated: v }),

      clearAuth: () =>
        set({
          accessToken: null,
          user: null,
          organization: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "wexaai-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        organization: state.organization,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
