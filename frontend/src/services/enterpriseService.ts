import { apiClient } from "./apiClient";

export interface TeamSummary {
  id: number;
  name: string;
  description?: string | null;
  owner_id: number;
}

export interface UserSummary {
  id: number;
  name: string;
  email?: string | null;
}

export async function fetchTeams(): Promise<TeamSummary[]> {
  const { data } = await apiClient.get<TeamSummary[]>("/enterprise/teams");
  return data;
}

export async function fetchUsers(): Promise<UserSummary[]> {
  const { data } = await apiClient.get<UserSummary[]>("/enterprise/users");
  return data;
}

export async function createTeam(name: string, description?: string) {
  return apiClient.post("/enterprise/teams", { name, description });
}

export async function createShare(payload: Record<string, unknown>) {
  return apiClient.post("/enterprise/shares", payload);
}

export async function addTeamMember(teamId: number, userId: number, role: string) {
  return apiClient.post(`/enterprise/teams/${teamId}/members`, { user_id: userId, role });
}

export async function createSchedule(payload: Record<string, unknown>) {
  return apiClient.post("/enterprise/schedules", payload);
}

export async function createAlert(payload: Record<string, unknown>) {
  return apiClient.post("/enterprise/alerts", payload);
}

export async function fetchAuditLogs() {
  const { data } = await apiClient.get("/enterprise/audit-logs");
  return data;
}

export async function createVersionSnapshot(dashboardId: number, versionLabel: string) {
  return apiClient.post(`/enterprise/version-history?dashboard_id=${dashboardId}&version_label=${encodeURIComponent(versionLabel)}`);
}

export async function fetchVersionHistory(dashboardId: number) {
  const { data } = await apiClient.get(`/enterprise/version-history/${dashboardId}`);
  return data;
}

export async function fetchSharedDashboards() {
  const { data } = await apiClient.get(`/enterprise/shared-dashboards`);
  return data;
}

export interface TeamMemberSummary {
  id: number;
  user_id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export async function fetchTeamMembers(teamId: number): Promise<TeamMemberSummary[]> {
  const { data } = await apiClient.get<TeamMemberSummary[]>(`/enterprise/teams/${teamId}/members`);
  return data;
}
