import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  listSavedDashboards,
  duplicateSavedDashboard,
  deleteSavedDashboard,
  updateSavedDashboard,
  type SavedDashboardSummary,
} from "../services/dashboardService";
import AuthStatus from "../components/AuthStatus";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function SavedDashboards() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [draftName, setDraftName] = useState("");

  const { data: dashboards, isLoading, isError } = useQuery({
    queryKey: ["saved-dashboards"],
    queryFn: () => listSavedDashboards(),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["saved-dashboards"] });
  }

  const duplicateMutation = useMutation({
    mutationFn: (id: number) => duplicateSavedDashboard(id),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSavedDashboard(id),
    onSuccess: invalidate,
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      updateSavedDashboard(id, { name }),
    onSuccess: () => {
      invalidate();
      setRenamingId(null);
    },
  });

  function startRename(dashboard: SavedDashboardSummary) {
    setRenamingId(dashboard.id);
    setDraftName(dashboard.name);
  }

  function commitRename(id: number) {
    if (draftName.trim()) {
      renameMutation.mutate({ id, name: draftName.trim() });
    } else {
      setRenamingId(null);
    }
  }

  return (
    <div className="min-h-screen px-6 py-10 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-semibold">My Dashboards</h1>
          <p className="text-scimly-muted text-sm">Saved dashboards from every uploaded file</p>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/upload" className="text-scimly-primary text-sm hover:underline">
            ← Back to Upload
          </Link>
          <AuthStatus />
        </div>
      </div>

      {isLoading && <p className="text-scimly-muted">Loading your dashboards…</p>}

      {isError && (
        <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/30 rounded-lg px-4 py-3">
          Couldn't load your saved dashboards.
        </p>
      )}

      {dashboards && dashboards.length === 0 && (
        <div className="text-scimly-muted bg-scimly-surface border border-scimly-border rounded-xl px-6 py-8 text-center">
          <p className="mb-2">No saved dashboards yet.</p>
          <p className="text-sm">
            Open a dataset's dashboard and hit <span className="text-scimly-text">Save</span> to
            keep it here.
          </p>
        </div>
      )}

      {dashboards && dashboards.length > 0 && (
        <ul className="space-y-3">
          {dashboards.map((dashboard) => (
            <li
              key={dashboard.id}
              className="flex items-center justify-between gap-4 bg-scimly-surface border border-scimly-border rounded-xl px-5 py-4"
            >
              <div className="min-w-0 flex-1">
                {renamingId === dashboard.id ? (
                  <input
                    autoFocus
                    value={draftName}
                    onChange={(e) => setDraftName(e.target.value)}
                    onBlur={() => commitRename(dashboard.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") commitRename(dashboard.id);
                      if (e.key === "Escape") setRenamingId(null);
                    }}
                    className="bg-scimly-bg border border-scimly-border rounded px-2 py-1 text-scimly-text text-sm w-full max-w-xs"
                  />
                ) : (
                  <button
                    onClick={() => navigate(`/dashboard/${dashboard.file_id}/saved/${dashboard.id}`)}
                    className="font-medium text-scimly-text hover:text-scimly-primary truncate text-left"
                    title="Open"
                  >
                    {dashboard.name}
                  </button>
                )}
                <p className="text-scimly-muted text-xs mt-1 truncate">
                  {dashboard.file_name ?? `File #${dashboard.file_id}`} · {dashboard.widget_count}{" "}
                  widget{dashboard.widget_count === 1 ? "" : "s"} · updated{" "}
                  {formatDate(dashboard.updated_at)}
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0 text-sm">
                <button
                  onClick={() => navigate(`/dashboard/${dashboard.file_id}/saved/${dashboard.id}`)}
                  className="px-3 py-1.5 rounded-lg border border-scimly-primary text-scimly-primary"
                >
                  Open
                </button>
                <button
                  onClick={() => startRename(dashboard)}
                  className="px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-muted hover:text-scimly-text"
                >
                  Rename
                </button>
                <button
                  onClick={() => duplicateMutation.mutate(dashboard.id)}
                  disabled={duplicateMutation.isPending}
                  className="px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-muted hover:text-scimly-text disabled:opacity-50"
                >
                  Duplicate
                </button>
                <button
                  onClick={() => {
                    if (confirm(`Delete "${dashboard.name}"? This can't be undone.`)) {
                      deleteMutation.mutate(dashboard.id);
                    }
                  }}
                  disabled={deleteMutation.isPending}
                  className="px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-muted hover:text-red-400 disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
