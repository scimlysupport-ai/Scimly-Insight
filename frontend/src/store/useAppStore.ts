import { create } from "zustand";

// Minimal global store to prove Zustand is wired up.
// Later phases will add: uploadedFiles, currentDataset, dashboardLayout, filters, etc.
interface AppState {
  backendStatus: "unknown" | "connected" | "error";
  setBackendStatus: (status: AppState["backendStatus"]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  backendStatus: "unknown",
  setBackendStatus: (status) => set({ backendStatus: status }),
}));
