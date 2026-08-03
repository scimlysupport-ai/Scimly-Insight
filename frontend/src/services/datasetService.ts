import { apiClient } from "./apiClient";

export interface UploadedFileResponse {
  id: number;
  original_filename: string;
  size_bytes: number;
  status: string;
  created_at: string;
}

export interface ColumnSchema {
  name: string;
  dtype: "numeric" | "categorical" | "datetime" | "boolean" | "text";
  stats: Record<string, unknown>;
}

export interface DatasetResponse {
  id: number;
  file_id: number;
  rows: number;
  columns: number;
  columns_schema: ColumnSchema[];
  created_at: string;
}

export interface ChartRecommendation {
  chart: "kpi" | "line" | "pie" | "bar" | "table";
  title: string;
  column?: string;
  x?: string;
  y?: string;
  value?: number;
  columns?: string[];
}

export interface RecommendationsResponse {
  recommendedCharts: ChartRecommendation[];
}

export interface AIInsight {
  title: string;
  text: string;
}

export interface AIInsightsResponse {
  insights: AIInsight[];
}

// Phase 9 — Global Filters
export interface DashboardFilters {
  categorical: Record<string, string[]>;
  date_ranges: Record<string, { start?: string; end?: string }>;
}

export function emptyFilters(): DashboardFilters {
  return { categorical: {}, date_ranges: {} };
}

export function hasActiveFilters(filters: DashboardFilters): boolean {
  return (
    Object.values(filters.categorical).some((values) => values.length > 0) ||
    Object.values(filters.date_ranges).some((range) => !!range.start || !!range.end)
  );
}

export interface CategoricalFilterOption {
  column: string;
  options: string[];
  // "tags": a delimiter-separated compound column (e.g. "Stale Admin;
  // Admin No Mfa") where each option is one individual tag, not a whole
  // compound string — filtering matches rows containing that tag, not
  // rows whose full string equals it.
  type: "categorical" | "tags";
}

export interface DateRangeFilterOption {
  column: string;
  min: string;
  max: string;
}

export interface FilterOptionsResponse {
  categorical: CategoricalFilterOption[];
  date_ranges: DateRangeFilterOption[];
}

export async function fetchFilterOptions(fileId: number): Promise<FilterOptionsResponse> {
  const { data } = await apiClient.get<FilterOptionsResponse>(`/dataset/${fileId}/filters`);
  return data;
}

export async function uploadFile(
  file: File,
  onProgress?: (percent: number) => void
): Promise<UploadedFileResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await apiClient.post<UploadedFileResponse>("/upload", formData, {
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });
  return data;
}

export async function fetchRecentUploads(): Promise<UploadedFileResponse[]> {
  const { data } = await apiClient.get<UploadedFileResponse[]>("/uploads");
  return data;
}

export async function deleteUpload(fileId: number): Promise<void> {
  await apiClient.delete(`/uploads/${fileId}`);
}

export interface DashboardWidget {
  chart: "kpi" | "line" | "pie" | "bar" | "table";
  title: string;
  column?: string;
  x?: string;
  y?: string;
  value?: number;
  columns?: string[];
  data: unknown;
}

export interface DashboardResponse {
  widgets: DashboardWidget[];
}

export async function fetchDataset(fileId: number): Promise<DatasetResponse> {
  const { data } = await apiClient.get<DatasetResponse>(`/dataset/${fileId}`);
  return data;
}

// Phase 13 — Large Dataset Support
export type ProcessingStage =
  | "uploaded" // small file, never queued — analyzed inline by fetchDataset
  | "queued"
  | "reading"
  | "cleaning"
  | "analyzing"
  | "saving"
  | "ready"
  | "failed";

export interface ProcessingProgress {
  status: ProcessingStage;
  progress: number; // 0-100
  message: string | null;
}

export function isProcessingDone(progress: ProcessingProgress | undefined): boolean {
  return !progress || progress.status === "ready" || progress.status === "uploaded";
}

export async function fetchProcessingProgress(fileId: number): Promise<ProcessingProgress> {
  const { data } = await apiClient.get<ProcessingProgress>(`/dataset/${fileId}/progress`);
  return data;
}

export async function fetchRecommendations(
  fileId: number
): Promise<RecommendationsResponse> {
  const { data } = await apiClient.get<RecommendationsResponse>(
    `/dataset/${fileId}/recommendations`
  );
  return data;
}

export async function fetchAIInsights(fileId: number): Promise<AIInsightsResponse> {
  const { data } = await apiClient.get<AIInsightsResponse>(`/dataset/${fileId}/insights`);
  return data;
}

export interface ChartPreviewRequest {
  chart: "kpi" | "line" | "pie" | "bar" | "table";
  column?: string;
  x?: string;
  y?: string;
  columns?: string[];
  filters?: DashboardFilters;
}

export interface ChartPreviewResponse {
  chart: string;
  data: unknown;
}

export async function fetchChartPreview(
  fileId: number,
  request: ChartPreviewRequest
): Promise<ChartPreviewResponse> {
  const { data } = await apiClient.post<ChartPreviewResponse>(
    `/dataset/${fileId}/chart-preview`,
    request
  );
  return data;
}

export async function fetchDashboard(
  fileId: number,
  filters: DashboardFilters = emptyFilters()
): Promise<DashboardResponse> {
  const { data } = await apiClient.post<DashboardResponse>(
    `/dataset/${fileId}/dashboard`,
    filters
  );
  return data;
}