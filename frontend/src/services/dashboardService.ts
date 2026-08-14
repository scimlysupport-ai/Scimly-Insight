import { apiClient } from "./apiClient";
import type { DashboardFilters, DashboardWidget } from "./datasetService";
import { emptyFilters } from "./datasetService";
import type { LayoutItem } from "../store/useLayoutStore";

// Phase 10 — Save Dashboard.
// A SavedWidget is a widget's full, final definition (chart/title/
// column choices/color already decided) — unlike DashboardWidget it
// carries no `data`; data gets re-fetched live via fetchWidgetsData so
// a saved dashboard always reflects the current dataset.
export interface SavedWidget {
  chart: DashboardWidget["chart"];
  title: string;
  column?: string;
  x?: string;
  y?: string;
  columns?: string[];
  color?: string;
  important?: boolean;
  agg?: string;
  entity_column?: string;
  measure?: string;
  top_n?: number;
  granularity?: string;
  rate_column?: string;
  rate_value?: string;
  count_kpi?: boolean;
  sort_by?: string;
}

export interface SavedDashboardResponse {
  id: number;
  file_id: number;
  name: string;
  widgets: SavedWidget[];
  layout: LayoutItem[];
  filters: DashboardFilters;
  created_at: string;
  updated_at: string;
}

export interface SavedDashboardSummary {
  id: number;
  file_id: number;
  file_name?: string;
  name: string;
  widget_count: number;
  created_at: string;
  updated_at: string;
}

export interface SaveDashboardPayload {
  file_id: number;
  name: string;
  widgets: SavedWidget[];
  layout: LayoutItem[];
  filters: DashboardFilters;
}

export async function createSavedDashboard(
  payload: SaveDashboardPayload
): Promise<SavedDashboardResponse> {
  const { data } = await apiClient.post<SavedDashboardResponse>("/dashboards", payload);
  return data;
}

export async function listSavedDashboards(fileId?: number): Promise<SavedDashboardSummary[]> {
  const { data } = await apiClient.get<SavedDashboardSummary[]>("/dashboards", {
    params: fileId ? { file_id: fileId } : undefined,
  });
  return data;
}

export async function fetchSavedDashboard(dashboardId: number): Promise<SavedDashboardResponse> {
  const { data } = await apiClient.get<SavedDashboardResponse>(`/dashboards/${dashboardId}`);
  return data;
}

export async function updateSavedDashboard(
  dashboardId: number,
  patch: Partial<Omit<SaveDashboardPayload, "file_id">>
): Promise<SavedDashboardResponse> {
  const { data } = await apiClient.put<SavedDashboardResponse>(`/dashboards/${dashboardId}`, patch);
  return data;
}

export async function duplicateSavedDashboard(
  dashboardId: number,
  name?: string
): Promise<SavedDashboardResponse> {
  const { data } = await apiClient.post<SavedDashboardResponse>(
    `/dashboards/${dashboardId}/duplicate`,
    { name }
  );
  return data;
}

export async function deleteSavedDashboard(dashboardId: number): Promise<void> {
  await apiClient.delete(`/dashboards/${dashboardId}`);
}

export interface WidgetsDataResponse {
  widgets: DashboardWidget[];
}

// Re-hydrates a saved widget list with live data from the current
// dataset (respecting whatever filters are active right now).
export async function fetchWidgetsData(
  fileId: number,
  widgets: SavedWidget[],
  filters: DashboardFilters = emptyFilters()
): Promise<WidgetsDataResponse> {
  const { data } = await apiClient.post<WidgetsDataResponse>(`/dataset/${fileId}/widgets-data`, {
    widgets,
    filters,
  });
  return data;
}
