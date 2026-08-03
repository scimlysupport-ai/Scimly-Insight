import { useEffect, useState, type MouseEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import DropZone from "../components/DropZone";
import AuthStatus from "../components/AuthStatus";
import {
  uploadFile,
  fetchRecentUploads,
  fetchDataset,
  fetchRecommendations,
  fetchAIInsights,
  fetchProcessingProgress,
  deleteUpload,
} from "../services/datasetService";

export default function Upload() {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [activeFileId, setActiveFileId] = useState<number | null>(null);
  // Phase 13 — set only while a *large* file is being analyzed in the
  // background; drives the processing-progress poll below and disables
  // the DropZone so a second upload can't be queued mid-analysis.
  const [processingFileId, setProcessingFileId] = useState<number | null>(null);

  const { data: recentUploads } = useQuery({
    queryKey: ["uploads"],
    queryFn: fetchRecentUploads,
  });

  // Phase 13 — polls GET /dataset/{id}/progress every second while a
  // large upload is being analyzed by the Celery worker. Stops polling
  // once the background job reaches a terminal state (ready/failed) —
  // there'd be nothing new to report after that.
  const { data: processingProgress } = useQuery({
    queryKey: ["processing-progress", processingFileId],
    queryFn: () => fetchProcessingProgress(processingFileId!),
    enabled: processingFileId !== null,
    refetchInterval: (query) => {
      const latest = query.state.data;
      if (!latest) return 1000;
      return latest.status === "ready" || latest.status === "failed" ? false : 1000;
    },
  });

  const { data: dataset } = useQuery({
    queryKey: ["dataset", activeFileId],
    queryFn: () => fetchDataset(activeFileId!),
    enabled: activeFileId !== null && processingFileId === null,
  });

  const { data: recommendations } = useQuery({
    queryKey: ["recommendations", activeFileId],
    queryFn: () => fetchRecommendations(activeFileId!),
    enabled: !!dataset,
  });

  const { data: aiInsights } = useQuery({
    queryKey: ["ai-insights", activeFileId],
    queryFn: () => fetchAIInsights(activeFileId!),
    enabled: !!dataset,
  });

  // Phase 13 — once the background job for a large file finishes, pull
  // the now-ready dataset/recommendations and stop polling. A failure
  // surfaces as an error instead of hanging on "Analyzing your file...".
  useEffect(() => {
    if (!processingProgress || processingFileId === null) return;

    if (processingProgress.status === "ready") {
      const fileId = processingFileId;
      setProcessingFileId(null);
      queryClient.invalidateQueries({ queryKey: ["uploads"] });
      queryClient
        .fetchQuery({ queryKey: ["dataset", fileId], queryFn: () => fetchDataset(fileId) })
        .then(() =>
          queryClient.fetchQuery({
            queryKey: ["recommendations", fileId],
            queryFn: () => fetchRecommendations(fileId),
          })
        )
        .then(() => setStatusMessage("Analysis complete."))
        .catch((analysisError: any) => {
          const detail = analysisError?.response?.data?.detail;
          setStatusMessage(
            detail
              ? `Processing finished, but analysis could not be completed: ${detail}`
              : "Processing finished, but analysis is still being prepared."
          );
        });
    } else if (processingProgress.status === "failed") {
      setProcessingFileId(null);
      setError(processingProgress.message ?? "Background processing failed for this file.");
      queryClient.invalidateQueries({ queryKey: ["uploads"] });
    }
  }, [processingProgress, processingFileId, queryClient]);

  async function handleFileSelected(file: File) {
    setError(null);
    setStatusMessage(null);
    setProgress(0);

    try {
      const result = await uploadFile(file, setProgress);
      setProgress(null);
      setActiveFileId(result.id);
      queryClient.invalidateQueries({ queryKey: ["uploads"] });

      // Phase 13 — large files come back with status "processing": the
      // upload endpoint has already queued a background Celery task, and
      // there's no Dataset row to fetch yet. Start polling progress
      // instead of calling fetchDataset (it would 202 until the worker
      // finishes).
      if (result.status === "processing") {
        setProcessingFileId(result.id);
        setStatusMessage(
          `Uploaded ${result.original_filename}. This is a large file, so it's being processed in the background...`
        );
        return;
      }

      setStatusMessage(`Uploaded ${result.original_filename}. Analyzing your file...`);
      try {
        await queryClient.fetchQuery({
          queryKey: ["dataset", result.id],
          queryFn: () => fetchDataset(result.id),
        });
        await queryClient.fetchQuery({
          queryKey: ["recommendations", result.id],
          queryFn: () => fetchRecommendations(result.id),
        });
        setStatusMessage(`Analysis complete for ${result.original_filename}.`);
      } catch (analysisError: any) {
        const detail = analysisError?.response?.data?.detail;
        setStatusMessage(
          detail ? `Upload succeeded, but analysis could not be completed: ${detail}` : "Upload succeeded, but analysis is still being prepared."
        );
      }
    } catch (err: any) {
      setProgress(null);
      const detail = err?.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : detail
          ? JSON.stringify(detail)
          : "Upload failed. Please try again."
      );
    }
  }

  async function handleDeleteUpload(fileId: number, event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    try {
      await deleteUpload(fileId);
      queryClient.removeQueries({ queryKey: ["dataset", fileId] });
      queryClient.removeQueries({ queryKey: ["recommendations", fileId] });
      queryClient.removeQueries({ queryKey: ["ai-insights", fileId] });
      queryClient.invalidateQueries({ queryKey: ["uploads"] });
      if (activeFileId === fileId) {
        setActiveFileId(null);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Could not delete upload.");
    }
  }

  return (
    <div className="min-h-screen px-6 py-12 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-1">
        <h1 className="font-display text-2xl font-semibold">Upload a dataset</h1>
        <AuthStatus />
      </div>
      <p className="text-scimly-muted text-sm mb-8">
        Upload a CSV or Excel file to get started.
      </p>

      <DropZone
        onFileSelected={handleFileSelected}
        disabled={progress !== null || processingFileId !== null}
      />

      {progress !== null && (
        <div className="mt-4">
          <div className="w-full h-2 bg-scimly-surface rounded-full overflow-hidden">
            <div
              className="h-full bg-scimly-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-scimly-muted text-xs mt-1">{progress}% uploaded</p>
        </div>
      )}

      {/* Phase 13 — background-processing progress for large files, shown
          right after the upload-transfer bar above finishes. */}
      {processingFileId !== null && (
        <div className="mt-4">
          <div className="w-full h-2 bg-scimly-surface rounded-full overflow-hidden">
            <div
              className="h-full bg-scimly-accent transition-all"
              style={{ width: `${processingProgress?.progress ?? 0}%` }}
            />
          </div>
          <p className="text-scimly-muted text-xs mt-1">
            {processingProgress?.message ?? "Queued for background processing…"}
            {typeof processingProgress?.progress === "number" ? ` (${processingProgress.progress}%)` : ""}
          </p>
        </div>
      )}

      {error && (
        <p className="mt-4 text-red-400 text-sm bg-red-400/10 border border-red-400/30 rounded-lg px-4 py-2">
          {error}
        </p>
      )}

      {statusMessage && !error && (
        <p className="mt-4 text-scimly-accent text-sm bg-scimly-primary/10 border border-scimly-primary/20 rounded-lg px-4 py-2">
          {statusMessage}
        </p>
      )}

      {dataset && (
        <div className="mt-8 bg-scimly-surface border border-scimly-border rounded-xl p-5">
          <h2 className="font-medium mb-3">Dataset summary</h2>
          <div className="flex gap-6 text-sm mb-4">
            <span className="text-scimly-muted">
              Rows: <span className="text-scimly-text">{dataset.rows}</span>
            </span>
            <span className="text-scimly-muted">
              Columns: <span className="text-scimly-text">{dataset.columns}</span>
            </span>
          </div>
          <div className="space-y-1 text-sm">
            {dataset.columns_schema.map((col) => (
              <div key={col.name} className="flex justify-between border-b border-scimly-border/50 py-1">
                <span>{col.name}</span>
                <span className="text-scimly-accent">{col.dtype}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {aiInsights && aiInsights.insights.length > 0 && (
        <div className="mt-4 bg-scimly-surface border border-scimly-border rounded-xl p-5">
          <h2 className="font-medium mb-3">AI insights</h2>
          <div className="space-y-3 text-sm">
            {aiInsights.insights.map((insight, index) => (
              <div key={`${insight.title}-${index}`} className="border-b border-scimly-border/50 pb-3 last:border-b-0 last:pb-0">
                <p className="font-medium text-scimly-text">{insight.title}</p>
                <p className="text-scimly-muted mt-1">{insight.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {recommendations && (
        <div className="mt-4 bg-scimly-surface border border-scimly-border rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium">
              Recommended charts ({recommendations.recommendedCharts.length})
            </h2>
            {activeFileId && (
              <Link
                to={`/dashboard/${activeFileId}`}
                className="text-scimly-primary text-sm hover:underline"
              >
                View full dashboard →
              </Link>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {recommendations.recommendedCharts.map((rec, i) => (
              <div key={i} className="bg-scimly-bg border border-scimly-border rounded-lg px-3 py-2">
                <span className="text-scimly-accent uppercase text-xs">{rec.chart}</span>
                <p className="text-scimly-text">{rec.title}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {recentUploads && recentUploads.length > 0 && (
        <div className="mt-10">
          <h2 className="text-sm text-scimly-muted uppercase tracking-wide mb-3">
            Recent uploads
          </h2>
          <div className="space-y-2">
            {recentUploads.map((upload) => (
              <div
                key={upload.id}
                className={`flex items-center gap-2 rounded-lg border transition-colors ${
                  activeFileId === upload.id
                    ? "border-scimly-primary bg-scimly-primary/5"
                    : "border-scimly-border hover:border-scimly-primary/40"
                }`}
              >
                <button
                  onClick={() => {
                    setActiveFileId(upload.id);
                    // Phase 13 — a large file selected from Recent Uploads
                    // might still be processing in the background from an
                    // earlier session; resume polling instead of letting
                    // the dataset query 202 against it.
                    setProcessingFileId(upload.status === "processing" ? upload.id : null);
                  }}
                  className="flex-1 text-left px-4 py-3"
                >
                  <div className="flex justify-between text-sm">
                    <span>{upload.original_filename}</span>
                    <span className="text-scimly-muted">{upload.status}</span>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={(event) => handleDeleteUpload(upload.id, event)}
                  className="mr-3 text-xs text-red-400 hover:text-red-300"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
