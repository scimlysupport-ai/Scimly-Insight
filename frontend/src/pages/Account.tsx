import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchRecentUploads } from "../services/datasetService";
import { listSavedDashboards } from "../services/dashboardService";
import { useAuthStore } from "../store/useAuthStore";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function Account() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logOut = useAuthStore((s) => s.logOut);

  const { data: uploads } = useQuery({
    queryKey: ["uploads"],
    queryFn: fetchRecentUploads,
    enabled: !!user,
  });

  const { data: dashboards } = useQuery({
    queryKey: ["saved-dashboards"],
    queryFn: () => listSavedDashboards(),
    enabled: !!user,
  });

  if (!user) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
        <p className="text-scimly-muted mb-4">You're not logged in.</p>
        <Link to="/login" className="text-scimly-primary hover:underline">
          Log in →
        </Link>
      </div>
    );
  }

  const [imgError, setImgError] = useState(false);
  const showAvatar = user.avatar_url && !imgError;

  return (
    <div className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <div className="mb-6">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-scimly-muted hover:text-scimly-primary transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-3.5 h-3.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Back to Home
        </Link>
      </div>

      <div className="flex items-center justify-between mb-8 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          {showAvatar ? (
            <img
              src={user.avatar_url!}
              alt=""
              className="w-12 h-12 rounded-full"
              onError={() => setImgError(true)}
            />
          ) : (
            <span className="w-12 h-12 rounded-full bg-scimly-primary/20 text-scimly-primary flex items-center justify-center text-lg font-medium">
              {(user.name || user.email || "?").charAt(0).toUpperCase()}
            </span>
          )}
          <div>
            <h1 className="font-display text-xl font-semibold">{user.name || "Your account"}</h1>
            <p className="text-scimly-muted text-sm">{user.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/upload" className="text-scimly-primary text-sm hover:underline">
            Upload a dataset
          </Link>
          <button
            onClick={() => {
              logOut();
              navigate("/");
            }}
            className="text-sm px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-muted hover:text-red-400"
          >
            Log out
          </button>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="text-sm font-medium text-scimly-muted mb-3 uppercase tracking-wide">
          Recent uploads
        </h2>
        {uploads && uploads.length === 0 && (
          <p className="text-scimly-muted text-sm">No uploads yet.</p>
        )}
        {uploads && uploads.length > 0 && (
          <ul className="space-y-2">
            {uploads.map((file) => (
              <li
                key={file.id}
                className="flex items-center justify-between bg-scimly-surface border border-scimly-border rounded-xl px-4 py-3"
              >
                <span className="truncate text-sm">{file.original_filename}</span>
                <Link
                  to={`/dashboard/${file.id}`}
                  className="text-scimly-primary text-sm hover:underline shrink-0"
                >
                  Open dashboard →
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-scimly-muted uppercase tracking-wide">
            Saved dashboards
          </h2>
          <Link to="/dashboards" className="text-scimly-primary text-sm hover:underline">
            View all →
          </Link>
        </div>
        {dashboards && dashboards.length === 0 && (
          <p className="text-scimly-muted text-sm">No saved dashboards yet.</p>
        )}
        {dashboards && dashboards.length > 0 && (
          <ul className="space-y-2">
            {dashboards.slice(0, 5).map((d) => (
              <li
                key={d.id}
                className="flex items-center justify-between bg-scimly-surface border border-scimly-border rounded-xl px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{d.name}</p>
                  <p className="text-scimly-muted text-xs">updated {formatDate(d.updated_at)}</p>
                </div>
                <Link
                  to={`/dashboard/${d.file_id}/saved/${d.id}`}
                  className="text-scimly-primary text-sm hover:underline shrink-0"
                >
                  Open →
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
