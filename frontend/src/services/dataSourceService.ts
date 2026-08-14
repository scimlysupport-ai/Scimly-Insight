import { apiClient } from "./apiClient";
import type { DashboardFilters, DatasetResponse, DashboardResponse, AIInsightsResponse, ChartPreviewRequest, ChartPreviewResponse } from "./datasetService";

export type DataSourceType =
  | "postgres"
  | "mysql"
  | "sqlserver"
  | "oracle"
  | "mongodb"
  | "google_sheets"
  | "rest_api";

export interface DataSourceResponse {
  id: number;
  name: string;
  source_type: DataSourceType;
  config: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface CreateDataSourceRequest {
  name: string;
  source_type: DataSourceType;
  config: Record<string, unknown>;
}

export async function createDataSource(
  request: CreateDataSourceRequest
): Promise<DataSourceResponse> {
  const { data } = await apiClient.post<DataSourceResponse>("/datasources", request);
  return data;
}

export async function fetchDataSources(): Promise<DataSourceResponse[]> {
  const { data } = await apiClient.get<DataSourceResponse[]>("/datasources");
  return data;
}

export async function fetchDataSource(sourceId: number): Promise<DataSourceResponse> {
  const { data } = await apiClient.get<DataSourceResponse>(`/datasources/${sourceId}`);
  return data;
}

export async function fetchDataSourceDataset(sourceId: number): Promise<DatasetResponse> {
  const { data } = await apiClient.get<DatasetResponse>(`/datasources/${sourceId}/dataset`);
  return data;
}

export async function fetchDataSourceRecommendations(sourceId: number): Promise<{ recommendedCharts: unknown[] }> {
  const { data } = await apiClient.get<{ recommendedCharts: unknown[] }>(`/datasources/${sourceId}/recommendations`);
  return data;
}

export async function fetchDataSourceFilterOptions(sourceId: number): Promise<unknown> {
  const { data } = await apiClient.get<unknown>(`/datasources/${sourceId}/filters`);
  return data;
}

export async function fetchDataSourceDashboard(
  sourceId: number,
  filters: DashboardFilters
): Promise<DashboardResponse> {
  const { data } = await apiClient.post<DashboardResponse>(`/datasources/${sourceId}/dashboard`, filters);
  return data;
}

export async function fetchDataSourceChartPreview(
  sourceId: number,
  request: ChartPreviewRequest
): Promise<ChartPreviewResponse> {
  const { data } = await apiClient.post<ChartPreviewResponse>(`/datasources/${sourceId}/chart-preview`, request);
  return data;
}

export async function fetchDataSourceAIInsights(sourceId: number): Promise<AIInsightsResponse> {
  const { data } = await apiClient.get<AIInsightsResponse>(`/datasources/${sourceId}/insights`);
  return data;
}

export interface DataSourceConfigField {
  name: string;
  label: string;
  placeholder?: string;
  type?: "text" | "password" | "number" | "textarea";
}

export function getDataSourceFields(sourceType: DataSourceType): DataSourceConfigField[] {
  switch (sourceType) {
    case "postgres":
    case "mysql":
    case "sqlserver":
    case "oracle":
      return [
        { name: "host", label: "Host", placeholder: "db.example.com" },
        { name: "port", label: "Port", type: "number", placeholder: "5432" },
        { name: "database", label: "Database", placeholder: "my_database" },
        { name: "username", label: "Username", placeholder: "db_user" },
        { name: "password", label: "Password", type: "password" },
        { name: "table", label: "Table (optional)", placeholder: "schema.table_name" },
        { name: "query", label: "SQL query (optional)", type: "textarea", placeholder: "SELECT * FROM table WHERE ..." },
      ];
    case "mongodb":
      return [
        { name: "uri", label: "Connection URI", type: "text", placeholder: "mongodb://user:pass@host:27017" },
        { name: "database", label: "Database", placeholder: "my_database" },
        { name: "collection", label: "Collection", placeholder: "my_collection" },
        { name: "filter", label: "Filter JSON", type: "textarea", placeholder: "{\"status\": \"active\"}" },
      ];
    case "google_sheets":
      return [
        { name: "sheet_url", label: "Google Sheet URL", placeholder: "https://docs.google.com/spreadsheets/d/..." },
        { name: "gid", label: "Sheet GID (optional)", placeholder: "0" },
      ];
    case "rest_api":
      return [
        { name: "url", label: "Endpoint URL", placeholder: "https://api.example.com/data" },
        { name: "method", label: "HTTP Method", placeholder: "GET" },
        { name: "auth_type", label: "Auth Type", placeholder: "none|bearer|basic" },
        { name: "auth_value", label: "Auth Value", placeholder: "token or username:password" },
        { name: "response_format", label: "Response Format", placeholder: "json|csv" },
      ];
    default:
      return [];
  }
}
