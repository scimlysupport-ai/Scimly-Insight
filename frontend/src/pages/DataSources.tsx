import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  createDataSource,
  fetchDataSources,
  getDataSourceFields,
  type DataSourceResponse,
  type DataSourceType,
} from "../services/dataSourceService";

const SOURCE_TYPES: { label: string; value: DataSourceType }[] = [
  { label: "PostgreSQL", value: "postgres" },
  { label: "MySQL", value: "mysql" },
  { label: "SQL Server", value: "sqlserver" },
  { label: "Oracle", value: "oracle" },
  { label: "MongoDB", value: "mongodb" },
  { label: "Google Sheets", value: "google_sheets" },
  { label: "REST API", value: "rest_api" },
];

export default function DataSources() {
  const queryClient = useQueryClient();
  const [sourceType, setSourceType] = useState<DataSourceType>("postgres");
  const [name, setName] = useState("");
  const [config, setConfig] = useState<Record<string, string>>({});
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeSourceId, setActiveSourceId] = useState<number | null>(null);

  const { data: sources, isLoading } = useQuery({
    queryKey: ["datasources"],
    queryFn: fetchDataSources,
  });

  const dataSourceFields = useMemo(() => getDataSourceFields(sourceType), [sourceType]);

  const createSourceMutation = useMutation<
    DataSourceResponse,
    Error,
    { name: string; source_type: DataSourceType; config: Record<string, unknown> }
  >({
    mutationFn: createDataSource,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["datasources"] });
      setActiveSourceId(data.id);
      setStatusMessage("Data source created and analyzed successfully.");
      setError(null);
    },
    onError: (response: any) => {
      setError(response?.response?.data?.detail ?? "Could not create data source.");
    },
  });

  useEffect(() => {
    if (!activeSourceId) return;
    queryClient.invalidateQueries({ queryKey: ["datasource-dataset", activeSourceId] });
    queryClient.invalidateQueries({ queryKey: ["datasource-recommendations", activeSourceId] });
  }, [activeSourceId, queryClient]);

  function handleConfigChange(field: string, value: string) {
    setConfig((current) => ({ ...current, [field]: value }));
  }

  const formFields = dataSourceFields.map((field) => (
    <label key={field.name} className="block text-sm text-scimly-muted mb-3">
      <span className="font-medium text-scimly-text">{field.label}</span>
      {field.type === "textarea" ? (
        <textarea
          value={config[field.name] ?? ""}
          onChange={(event) => handleConfigChange(field.name, event.target.value)}
          placeholder={field.placeholder}
          className="mt-1 w-full rounded-lg border border-scimly-border bg-scimly-bg px-3 py-2 text-sm text-scimly-text"
        />
      ) : (
        <input
          type={field.type ?? "text"}
          value={config[field.name] ?? ""}
          onChange={(event) => handleConfigChange(field.name, event.target.value)}
          placeholder={field.placeholder}
          className="mt-1 w-full rounded-lg border border-scimly-border bg-scimly-bg px-3 py-2 text-sm text-scimly-text"
        />
      )}
    </label>
  ));

  return (
    <div className="min-h-screen px-6 py-12 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-semibold">Connect a live datasource</h1>
          <p className="text-scimly-muted text-sm">Build dashboards directly from PostgreSQL, MySQL, SQL Server, Oracle, MongoDB, Google Sheets, or REST APIs.</p>
        </div>
        <Link to="/upload" className="text-scimly-primary text-sm hover:underline">Back to uploads</Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="bg-scimly-surface border border-scimly-border rounded-xl p-6">
          <h2 className="font-medium text-lg mb-4">New data source</h2>
          <div className="grid gap-4 mb-4 sm:grid-cols-2">
            <label className="block text-sm text-scimly-muted">
              <span className="font-medium text-scimly-text">Name</span>
              <input
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="My PostgreSQL database"
                className="mt-1 w-full rounded-lg border border-scimly-border bg-scimly-bg px-3 py-2 text-sm text-scimly-text"
              />
            </label>
            <label className="block text-sm text-scimly-muted">
              <span className="font-medium text-scimly-text">Source type</span>
              <select
                value={sourceType}
                onChange={(event) => setSourceType(event.target.value as DataSourceType)}
                className="mt-1 w-full rounded-lg border border-scimly-border bg-scimly-bg px-3 py-2 text-sm text-scimly-text"
              >
                {SOURCE_TYPES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {formFields}

          <button
            disabled={createSourceMutation.status === "pending"}
            onClick={() => {
              setError(null);
              setStatusMessage(null);
              if (!name.trim()) {
                setError("Please enter a name for the data source.");
                return;
              }
              createSourceMutation.mutate({ name, source_type: sourceType, config });
            }}
            className="mt-4 inline-flex items-center justify-center rounded-xl bg-scimly-primary px-5 py-2.5 text-sm font-medium text-white hover:bg-scimly-primary-dark disabled:opacity-50"
          >
            {createSourceMutation.status === "pending" ? "Connecting…" : "Connect source"}
          </button>

          {statusMessage && <p className="mt-4 text-green-500">{statusMessage}</p>}
          {error && <p className="mt-4 text-red-500">{error}</p>}
        </div>

        <div className="bg-scimly-surface border border-scimly-border rounded-xl p-6">
          <h2 className="font-medium text-lg mb-4">Your data sources</h2>
          {isLoading ? (
            <p className="text-scimly-muted">Loading…</p>
          ) : sources?.length ? (
            <div className="space-y-3">
              {sources.map((source) => (
                <button
                  key={source.id}
                  onClick={() => setActiveSourceId(source.id)}
                  className="w-full rounded-xl border border-scimly-border p-4 text-left hover:border-scimly-primary"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-medium text-scimly-text">{source.name}</p>
                      <p className="text-scimly-muted text-xs uppercase tracking-wide">{source.source_type.replace("_", " ")}</p>
                    </div>
                    <span className="text-scimly-accent text-sm">{source.status}</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-sm text-scimly-muted">No live data sources connected yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
