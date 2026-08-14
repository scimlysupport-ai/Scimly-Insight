import axios from "axios";
import { getDeviceId } from "./deviceId";
import { useAuthStore } from "../store/useAuthStore";

// Use environment variable in production, fallback to local dev proxy /api.
// Note: Vite requires literal `import.meta.env.VITE_API_URL` for static replacement during production build.
const isProduction = import.meta.env.PROD;
const apiBase = (import.meta.env.VITE_API_URL as string) || (isProduction ? "" : "/api");

// All backend calls go through this single client.
export const apiClient = axios.create({
  baseURL: apiBase,
});

// Phase 10 — every request carries this browser's anonymous device id,
// so the backend can scope saved dashboards to "whoever is asking".
apiClient.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  config.headers["X-Device-ID"] = getDeviceId();

  const token = useAuthStore.getState().token;
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }

  return config;
});
