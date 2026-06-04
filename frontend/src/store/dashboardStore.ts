import { create } from "zustand";
import type { Dashboard, Widget } from "@/types";

interface DashboardState {
  activeDashboard: Dashboard | null;
  isFullscreen: boolean;
  autoRefreshInterval: number | null;
  setActiveDashboard: (dashboard: Dashboard | null) => void;
  setFullscreen: (v: boolean) => void;
  setAutoRefreshInterval: (seconds: number | null) => void;
  updateWidget: (widgetId: string, updates: Partial<Widget>) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  activeDashboard: null,
  isFullscreen: false,
  autoRefreshInterval: null,

  setActiveDashboard: (dashboard) => set({ activeDashboard: dashboard }),

  setFullscreen: (v) => set({ isFullscreen: v }),

  setAutoRefreshInterval: (seconds) => set({ autoRefreshInterval: seconds }),

  updateWidget: (widgetId, updates) =>
    set((state) => {
      if (!state.activeDashboard) return state;
      return {
        activeDashboard: {
          ...state.activeDashboard,
          widgets: state.activeDashboard.widgets?.map((w) =>
            w.id === widgetId ? { ...w, ...updates } : w
          ),
        },
      };
    }),
}));
