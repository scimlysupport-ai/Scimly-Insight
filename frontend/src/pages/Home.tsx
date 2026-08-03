import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiClient } from "../services/apiClient";
import AuthStatus from "../components/AuthStatus";

interface HealthResponse {
  status: string;
  api: string;
  database: string;
}

async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}

export default function Home() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 relative">
      <div className="absolute top-6 right-6">
        <AuthStatus />
      </div>
      <h1 className="font-display text-4xl font-semibold text-scimly-text mb-2">
        Scimly
      </h1>
      <p className="text-scimly-muted mb-8">
        Phase 1 — Project Setup
      </p>

      <div className="bg-scimly-surface border border-scimly-border rounded-xl px-6 py-5 w-full max-w-md">
        <h2 className="text-sm font-medium text-scimly-muted mb-3 uppercase tracking-wide">
          System status
        </h2>

        {isLoading && (
          <p className="text-scimly-muted">Checking backend connection…</p>
        )}

        {isError && (
          <p className="text-red-400">
            Could not reach the backend. Is FastAPI running on port 8000?
          </p>
        )}

        {data && (
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-scimly-muted">API</span>
              <span className="text-scimly-accent">{data.api}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-scimly-muted">Database</span>
              <span className="text-scimly-accent">{data.database}</span>
            </li>
          </ul>
        )}
      </div>

      <div className="mt-6 flex items-center gap-4">
        <Link to="/upload" className="text-scimly-primary text-sm hover:underline">
          Go to Upload →
        </Link>
        <Link to="/dashboards" className="text-scimly-muted text-sm hover:text-scimly-text hover:underline">
          My Dashboards
        </Link>
      </div>
    </div>
  );
}
