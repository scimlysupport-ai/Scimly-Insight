import axios from "axios";
import { getDeviceId } from "./deviceId";
import { useAuthStore } from "../store/useAuthStore";

// Use environment variable in production, fallback to local dev proxy /api
const isProduction = import.meta.env.PROD;
const apiBase = import.meta.env.VITE_API_URL || (isProduction ? "" : "/api");

// All backend calls go through this single client.
export const apiClient = axios.create({
  baseURL: apiBase,
});

// Phase 10 — every request carries this browser's anonymous device id,
// so the backend can scope saved dashboards to "whoever is asking".
// Phase 12 — if someone's logged in, we also (or instead) send their
// JWT; the backend's shared dependency (app/api/deps.py) prefers the
// Bearer token and falls back to X-Device-Id, so sending both is safe.
apiClient.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  config.headers["X-Device-Id"] = getDeviceId();

  const token = useAuthStore.getState().token;
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

// Phase 12 — an expired/invalid token means the backend no longer
// recognizes this session. Clear it so the app quietly falls back to
// the anonymous device id instead of repeatedly failing requests.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && useAuthStore.getState().token) {
      useAuthStore.getState().logOut();
    }
    return Promise.reject(error);
  }
);
