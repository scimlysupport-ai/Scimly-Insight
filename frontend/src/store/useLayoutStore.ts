import { create } from "zustand";

export interface LayoutItem {
  i: string; // widget id
  x: number;
  y: number;
  w: number;
  h: number;
}

interface LayoutState {
  // layouts[fileId] = LayoutItem[]
  layouts: Record<string, LayoutItem[]>;
  setLayout: (fileId: string, layout: LayoutItem[]) => void;
  resetLayout: (fileId: string) => void;
  getLayout: (fileId: string) => LayoutItem[] | undefined;
}

const STORAGE_KEY = "scimly_dashboard_layouts";

function loadFromStorage(): Record<string, LayoutItem[]> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveToStorage(layouts: Record<string, LayoutItem[]>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(layouts));
  } catch {
    // Storage full or unavailable — layout just won't persist across reloads.
  }
}

export const useLayoutStore = create<LayoutState>((set, get) => ({
  layouts: loadFromStorage(),

  setLayout: (fileId, layout) => {
    set((state) => {
      const next = { ...state.layouts, [fileId]: layout };
      saveToStorage(next);
      return { layouts: next };
    });
  },

  resetLayout: (fileId) => {
    set((state) => {
      const next = { ...state.layouts };
      delete next[fileId];
      saveToStorage(next);
      return { layouts: next };
    });
  },

  getLayout: (fileId) => get().layouts[fileId],
}));
