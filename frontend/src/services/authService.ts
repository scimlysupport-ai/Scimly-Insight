import { apiClient } from "./apiClient";
import { getDeviceId } from "./deviceId";

// Phase 12 — Authentication.
export interface AuthUser {
  id: number;
  email: string | null;
  name: string | null;
  avatar_url: string | null;
  auth_provider: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export async function registerAccount(
  email: string,
  password: string,
  name?: string
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/register", {
    email,
    password,
    name: name || undefined,
  });
  return data;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  return data;
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await apiClient.get<AuthUser>("/auth/me");
  return data;
}

// Helper to resolve absolute API URL for full-page OAuth redirects
const isProduction = import.meta.env.PROD;
const rawApiBase = (import.meta.env.VITE_API_URL as string) || (isProduction ? "" : "/api");

function getOAuthBaseUrl(): string {
  const cleaned = rawApiBase.endsWith("/") ? rawApiBase.slice(0, -1) : rawApiBase;
  if (cleaned.endsWith("/api")) {
    return cleaned;
  }
  return `${cleaned}/api`;
}

export function googleLoginUrl(): string {
  const base = getOAuthBaseUrl();
  return `${base}/auth/google/login?device_id=${encodeURIComponent(getDeviceId())}`;
}

export function githubLoginUrl(): string {
  const base = getOAuthBaseUrl();
  return `${base}/auth/github/login?device_id=${encodeURIComponent(getDeviceId())}`;
}
