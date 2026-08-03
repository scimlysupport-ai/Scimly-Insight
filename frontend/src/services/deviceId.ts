// Phase 10 — Save Dashboard.
// There's no login yet (Phase 12), so each browser gets one anonymous
// id, generated once and kept in localStorage, sent as X-Device-Id on
// every request. The backend uses it to scope "my saved dashboards".
const STORAGE_KEY = "scimly_device_id";

export function getDeviceId(): string {
  try {
    const existing = localStorage.getItem(STORAGE_KEY);
    if (existing) return existing;

    const generated =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `device-${Date.now()}-${Math.random().toString(16).slice(2)}`;

    localStorage.setItem(STORAGE_KEY, generated);
    return generated;
  } catch {
    // localStorage unavailable (private browsing, etc.) — fall back to a
    // per-session id so requests still work, just without persistence.
    return `device-session-${Date.now()}`;
  }
}
