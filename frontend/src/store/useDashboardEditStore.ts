import { create } from "zustand";

export interface WidgetOverride {
  title?: string;
  deleted?: boolean;
  color?: string;
  chart?: "kpi" | "line" | "pie" | "bar" | "table";
  column?: string;
  x?: string;
  y?: string;
  columns?: string[];
}

interface DashboardEditState {
  editMode: boolean;
  // overrides[fileId][widgetId] = WidgetOverride
  overrides: Record<string, Record<string, WidgetOverride>>;
  toggleEditMode: () => void;
  setEditMode: (value: boolean) => void;
  updateWidget: (fileId: string, widgetId: string, patch: WidgetOverride) => void;
  deleteWidget: (fileId: string, widgetId: string) => void;
  resetDashboard: (fileId: string) => void;
  getOverride: (fileId: string, widgetId: string) => WidgetOverride | undefined;
}

const STORAGE_KEY = "scimly_dashboard_overrides";

function loadFromStorage(): Record<string, Record<string, WidgetOverride>> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveToStorage(overrides: Record<string, Record<string, WidgetOverride>>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(overrides));
  } catch {
    // Storage full or unavailable — edits just won't persist across reloads.
  }
}

export const useDashboardEditStore = create<DashboardEditState>((set, get) => ({
  editMode: false,
  overrides: loadFromStorage(),

  toggleEditMode: () => set((state) => ({ editMode: !state.editMode })),
  setEditMode: (value) => set({ editMode: value }),

  updateWidget: (fileId, widgetId, patch) => {
    set((state) => {
      const fileOverrides = { ...(state.overrides[fileId] ?? {}) };
      fileOverrides[widgetId] = { ...(fileOverrides[widgetId] ?? {}), ...patch };
      const next = { ...state.overrides, [fileId]: fileOverrides };
      saveToStorage(next);
      return { overrides: next };
    });
  },

  deleteWidget: (fileId, widgetId) => {
    get().updateWidget(fileId, widgetId, { deleted: true });
  },

  resetDashboard: (fileId) => {
    set((state) => {
      const next = { ...state.overrides };
      delete next[fileId];
      saveToStorage(next);
      return { overrides: next };
    });
  },

  getOverride: (fileId, widgetId) => {
    return get().overrides[fileId]?.[widgetId];
  },
}));
