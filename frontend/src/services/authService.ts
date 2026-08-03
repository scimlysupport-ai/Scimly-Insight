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

// OAuth is a full-page redirect flow, not an API call: the browser
// navigates to the backend, which redirects to Google/GitHub, which
// redirects back to the backend, which redirects to /auth/callback on
// the frontend with a token in the query string. We pass the current
// device id along so any anonymous uploads/dashboards on this browser
// get claimed by the resulting account (see claim_device_data on the
// backend).
export function googleLoginUrl(): string {
  return `/api/auth/google/login?device_id=${encodeURIComponent(getDeviceId())}`;
}

export function githubLoginUrl(): string {
  return `/api/auth/github/login?device_id=${encodeURIComponent(getDeviceId())}`;
}
