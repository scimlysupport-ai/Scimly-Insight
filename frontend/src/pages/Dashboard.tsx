import { useEffect, useMemo, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { useParams, useNavigate, useSearchParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchDashboard,
  fetchDataset,
  fetchFilterOptions,
  fetchProcessingProgress,
  emptyFilters,
  askScimly,
  type DashboardWidget,
  type DashboardFilters,
} from "../services/datasetService";
import {
  fetchSavedDashboard,
  fetchWidgetsData,
  createSavedDashboard,
  updateSavedDashboard,
  type SavedWidget,
} from "../services/dashboardService";
import FilterBar from "../components/FilterBar";
import EditableWidget from "../components/EditableWidget";
import ExportMenu from "../components/ExportMenu";
import AuthStatus from "../components/AuthStatus";
import { useDashboardEditStore } from "../store/useDashboardEditStore";
import { useLayoutStore, type LayoutItem } from "../store/useLayoutStore";
import { compactLayout, generateDefaultLayout, GRID_COLS, ROW_HEIGHT } from "../utils/layoutUtils";
import {
  exportWidgetsAsCSV,
  exportWidgetsAsExcel,
  exportWidgetsAsJSON,
  exportElementAsPNG,
  exportElementAsPDF,
} from "../utils/exportUtils";

interface InteractionState {
  widgetId: string;
  startPointer: { x: number; y: number };
  startItem: LayoutItem;
}

export default function Dashboard() {
  const { fileId, savedId } = useParams<{ fileId?: string; savedId?: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const paramFileId = fileId || searchParams.get("fileId") || "";
  const paramSavedId = savedId || searchParams.get("savedId") || "";

  const id = Number(paramFileId);
  const fileKey = String(id);

  // Phase 10 — opening a saved snapshot instead of the auto-generated
  // dashboard. isSavedMode drives which data source widgets come from
  // and which key their layout/edits are stored under (so two saved
  // dashboards on the same file never collide with each other or with
  // the unsaved auto dashboard).
  const savedIdNum = paramSavedId ? Number(paramSavedId) : NaN;
  const isSavedMode = !Number.isNaN(savedIdNum);
  const dashboardKey = isSavedMode ? `saved-${savedIdNum}` : fileKey;

  const editMode = useDashboardEditStore((s) => s.editMode);
  const toggleEditMode = useDashboardEditStore((s) => s.toggleEditMode);
  const resetDashboard = useDashboardEditStore((s) => s.resetDashboard);
  const updateWidget = useDashboardEditStore((s) => s.updateWidget);
  const overrides = useDashboardEditStore((s) => s.overrides[dashboardKey]);
  const [newWidgetType, setNewWidgetType] = useState<"kpi" | "line" | "pie" | "bar" | "table">("kpi");
  const [customWidgets, setCustomWidgets] = useState<DashboardWidget[]>([]);
  const [gridWidth, setGridWidth] = useState(1200);
  const [dragState, setDragState] = useState<InteractionState | null>(null);
  const [resizeState, setResizeState] = useState<InteractionState | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);
  const [chatPrompt, setChatPrompt] = useState("");
  const [chatPending, setChatPending] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const layoutRef = useRef<LayoutItem[]>([]);

  const savedLayout = useLayoutStore((s) => s.layouts[dashboardKey]);
  const setLayout = useLayoutStore((s) => s.setLayout);
  const resetLayout = useLayoutStore((s) => s.resetLayout);

  const [filters, setFilters] = useState<DashboardFilters>(emptyFilters());

  useEffect(() => {
    // Auto dashboards always start from a clean filter state. Saved
    // dashboards get their filters from the saved snapshot instead
    // (see the effect below), so skip resetting them here.
    if (!isSavedMode) setFilters(emptyFilters());
  }, [id, isSavedMode]);

  // Phase 13 — a file navigated to directly (bookmark, back button, a
  // link clicked right after upload) might still be a large file being
  // analyzed in the background. Check its status before asking for a
  // dashboard/filters/schema that don't exist yet, and keep polling
  // while it's still an active stage. Saved dashboards are excluded:
  // a dashboard can't have been saved against a file that was never
  // successfully analyzed, so there's nothing to gate there.
  const { data: processingStatus, isError: isProgressError, error: progressErrorObj } = useQuery({
    queryKey: ["processing-progress", id],
    queryFn: () => fetchProcessingProgress(id),
    enabled: !Number.isNaN(id) && !isSavedMode,
    refetchInterval: (query) => {
      const latest = query.state.data;
      if (!latest) return 1500;
      const active = latest.status !== "ready" && latest.status !== "uploaded" && latest.status !== "failed";
      return active ? 1500 : false;
    },
  });

  // Undefined (query hasn't resolved yet) is treated as "still blocked" —
  // safer to wait one extra round trip than to fire fetchDashboard/
  // fetchDataset against a file whose Dataset row may not exist yet.
  const isProcessingBlocked =
    !isSavedMode &&
    !isProgressError &&
    (!processingStatus || (processingStatus.status !== "ready" && processingStatus.status !== "uploaded"));

  const { data: filterOptions } = useQuery({
    queryKey: ["filters", id],
    queryFn: () => fetchFilterOptions(id),
    enabled: !Number.isNaN(id) && !isProcessingBlocked,
  });

  // Phase 10 — load the saved dashboard's widgets/layout/filters.
  const { data: savedDashboard, isLoading: savedLoading, isError: savedError } = useQuery({
    queryKey: ["saved-dashboard", savedIdNum],
    queryFn: () => fetchSavedDashboard(savedIdNum),
    enabled: isSavedMode,
  });

  // Seed filters + layout from the saved snapshot the first time it loads.
  useEffect(() => {
    if (savedDashboard && isSavedMode) {
      setFilters(savedDashboard.filters);
      if (!useLayoutStore.getState().layouts[dashboardKey]) {
        setLayout(dashboardKey, savedDashboard.layout);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedDashboard?.id]);

  const { data: autoDashboard, isLoading: autoLoading, isError: autoError, error: autoErrorObj } = useQuery({
    queryKey: ["dashboard", id, filters],
    queryFn: () => fetchDashboard(id, filters),
    enabled: !Number.isNaN(id) && !isSavedMode && !isProcessingBlocked,
  });

  // Phase 10 — re-hydrate the saved widget list with live data,
  // respecting whatever filters are currently active.
  const { data: savedWidgetsData, isLoading: savedWidgetsLoading, isError: savedWidgetsError } = useQuery({
    queryKey: ["saved-widgets-data", id, savedIdNum, savedDashboard?.widgets, filters],
    queryFn: () => fetchWidgetsData(id, savedDashboard!.widgets, filters),
    enabled: !Number.isNaN(id) && isSavedMode && !!savedDashboard,
  });

  const data = isSavedMode ? savedWidgetsData : autoDashboard;
  const isLoading = isSavedMode ? savedLoading || savedWidgetsLoading : autoLoading;
  const isError = isSavedMode ? savedError || savedWidgetsError : autoError;
  const error = autoErrorObj;

  const { data: dataset } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => fetchDataset(id),
    enabled: !Number.isNaN(id) && !isProcessingBlocked,
  });

  const widgetIdPrefix = isSavedMode ? "saved-widget" : "widget";

  const visibleWidgets = useMemo(() => {
    if (!data) return [];
    const baseWidgets = data.widgets.map((widget, i) => ({ id: `${widgetIdPrefix}-${i}`, widget }));
    const addedWidgets = customWidgets.map((widget, index) => ({
      id: `custom-widget-${index + 1}`,
      widget,
    }));
    return [...baseWidgets, ...addedWidgets].filter(({ id: widgetId }) => !overrides?.[widgetId]?.deleted);
  }, [data, overrides, customWidgets, widgetIdPrefix]);

  const layout: LayoutItem[] = useMemo(() => {
    const effectiveCols = gridWidth < 768 ? 1 : GRID_COLS;
    const defaults = generateDefaultLayout(
      visibleWidgets.map(({ id: widgetId, widget }) => ({ id: widgetId, chart: widget.chart })),
      effectiveCols
    );
    if (!savedLayout) return defaults;

    const savedById = new Map(savedLayout.map((item) => [item.i, item]));
    return defaults.map((def) => {
      const saved = savedById.get(def.i);
      if (!saved) return def;
      return {
        ...def,
        x: saved.x,
        y: saved.y,
        w: Math.max(1, Math.min(saved.w ?? def.w, effectiveCols)),
        h: saved.h ?? def.h,
      };
    });
  }, [visibleWidgets, savedLayout, gridWidth]);

  useEffect(() => {
    layoutRef.current = layout;
  }, [layout]);

  useEffect(() => {
    const node = gridRef.current;
    if (!node) return;

    const updateGridWidth = () => {
      setGridWidth(node.clientWidth || 1200);
    };

    updateGridWidth();
    const observer = new ResizeObserver(updateGridWidth);
    observer.observe(node);
    window.addEventListener("resize", updateGridWidth);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updateGridWidth);
    };
  }, []);

  useEffect(() => {
    if (!dragState && !resizeState) return;

    const handleMove = (event: MouseEvent) => {
      if (dragState) {
        const dx = event.clientX - dragState.startPointer.x;
        const dy = event.clientY - dragState.startPointer.y;
        const effectiveCols = gridWidth < 768 ? 1 : GRID_COLS;
        const cellWidth = gridWidth / effectiveCols;
        const nextX = Math.max(0, Math.min(effectiveCols - dragState.startItem.w, dragState.startItem.x + Math.round(dx / cellWidth)));
        const nextY = Math.max(0, dragState.startItem.y + Math.round(dy / ROW_HEIGHT));
        const nextLayout = layoutRef.current.map((item) =>
          item.i === dragState.widgetId ? { ...item, x: nextX, y: nextY } : item
        );
        layoutRef.current = nextLayout;
        setLayout(dashboardKey, nextLayout);
      }

      if (resizeState) {
        const dx = event.clientX - resizeState.startPointer.x;
        const dy = event.clientY - resizeState.startPointer.y;
        const effectiveCols = gridWidth < 768 ? 1 : GRID_COLS;
        const cellWidth = gridWidth / effectiveCols;
        const nextW = Math.max(1, Math.min(effectiveCols - resizeState.startItem.x, resizeState.startItem.w + Math.round(dx / cellWidth)));
        const nextH = Math.max(1, resizeState.startItem.h + Math.round(dy / ROW_HEIGHT));
        const nextLayout = layoutRef.current.map((item) =>
          item.i === resizeState.widgetId ? { ...item, w: nextW, h: nextH } : item
        );
        layoutRef.current = nextLayout;
        setLayout(dashboardKey, nextLayout);
      }
    };

    const handleUp = () => {
      const effectiveCols = gridWidth < 768 ? 1 : GRID_COLS;
      if (dragState) {
        const compacted = compactLayout(layoutRef.current, effectiveCols);
        layoutRef.current = compacted;
        setLayout(dashboardKey, compacted);
      }
      if (resizeState) {
        const compacted = compactLayout(layoutRef.current, effectiveCols);
        layoutRef.current = compacted;
        setLayout(dashboardKey, compacted);
      }
      setDragState(null);
      setResizeState(null);
    };

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);

    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
    };
  }, [dragState, resizeState, dashboardKey, gridWidth]);

  function startDrag(widgetId: string, event: ReactMouseEvent<HTMLElement>) {
    if (!editMode) return;
    event.preventDefault();
    event.stopPropagation();
    const item = layoutRef.current.find((entry) => entry.i === widgetId);
    if (!item) return;
    setDragState({ widgetId, startPointer: { x: event.clientX, y: event.clientY }, startItem: { ...item } });
  }

  function startResize(widgetId: string, event: ReactMouseEvent<HTMLElement>) {
    if (!editMode) return;
    event.preventDefault();
    event.stopPropagation();
    const item = layoutRef.current.find((entry) => entry.i === widgetId);
    if (!item) return;
    setResizeState({ widgetId, startPointer: { x: event.clientX, y: event.clientY }, startItem: { ...item } });
  }

  function cycleWidgetSize(widgetId: string) {
    if (!editMode) return;
    const effectiveCols = gridWidth < 768 ? 1 : GRID_COLS;
    const item = layoutRef.current.find((entry) => entry.i === widgetId);
    if (!item) return;

    const small = { w: Math.min(3, effectiveCols), h: 2 };
    const wide = { w: Math.min(6, effectiveCols), h: effectiveCols === 1 ? 2 : 3 };
    const full = { w: effectiveCols, h: effectiveCols === 1 ? 2 : 4 };

    const nextSize = (() => {
      if (item.w <= small.w && item.h <= small.h) return wide;
      if (item.w <= wide.w && item.h <= wide.h) return full;
      return small;
    })();

    const nextLayout = layoutRef.current.map((entry) =>
      entry.i === widgetId ? { ...entry, ...nextSize } : entry
    );
    const compacted = compactLayout(nextLayout, effectiveCols);
    layoutRef.current = compacted;
    setLayout(dashboardKey, compacted);
  }

  // Phase 10 — Save Dashboard. Bakes every visible widget's current
  // overrides into a final, self-contained widget list (no more
  // "override on top of a base widget" — that's just how *editing*
  // works; what gets saved is the resolved result).
  function computeEffectiveWidgets(): SavedWidget[] {
    return visibleWidgets.map(({ id: widgetId, widget }) => {
      const override = overrides?.[widgetId];
      const isTypeChanged = override?.chart !== undefined && override.chart !== widget.chart;

      if (isTypeChanged && override?.chart) {
        return {
          chart: override.chart,
          title: override.title ?? widget.title,
          column: override.column,
          x: override.x,
          y: override.y,
          columns: override.columns,
          color: override.color,
        } as SavedWidget;
      }

      return {
        chart: widget.chart,
        title: override?.title ?? widget.title,
        column: override?.column ?? widget.column,
        x: override?.x ?? widget.x,
        y: override?.y ?? widget.y,
        columns: override?.columns ?? widget.columns,
        color: override?.color ?? (widget as any).color,

        important: widget.important,
        agg: override?.y === undefined ? (override?.column === undefined ? widget.agg : undefined) : undefined,
        entity_column: widget.entity_column,
        measure: widget.measure,
        top_n: widget.top_n,
        granularity: widget.granularity,
        rate_column: widget.rate_column,
        rate_value: widget.rate_value,
        count_kpi: (override?.column !== undefined && override.column !== widget.column) ? false : widget.count_kpi,
        sort_by: widget.sort_by,
      } as SavedWidget;
    });
  }

  const createMutation = useMutation({
    mutationFn: createSavedDashboard,
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["saved-dashboards"] });
      setSaveState("saved");
      navigate(`/dashboard/${id}/saved/${created.id}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      updateSavedDashboard(savedIdNum, {
        widgets: computeEffectiveWidgets(),
        layout,
        filters,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-dashboard", savedIdNum] });
      queryClient.invalidateQueries({ queryKey: ["saved-dashboards"] });
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 1500);
    },
  });

  function handleSaveAs() {
    const defaultName = savedDashboard?.name ?? dataset?.columns_schema.length
      ? `${savedDashboard ? `${savedDashboard.name} (copy)` : "New dashboard"}`
      : "New dashboard";
    const name = window.prompt("Name this dashboard:", defaultName);
    if (!name) return;
    createMutation.mutate({
      file_id: id,
      name,
      widgets: computeEffectiveWidgets(),
      layout,
      filters,
    });
  }

  function handleSave() {
    if (isSavedMode) {
      updateMutation.mutate();
    } else {
      handleSaveAs();
    }
  }

  async function handleAskScimly(event: ReactMouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    if (!fileId || !chatPrompt.trim()) return;
    setChatPending(true);
    setChatError(null);
    try {
      const response = await askScimly(Number(fileId), chatPrompt.trim());
      setCustomWidgets((current) => [...current, response.widget]);
      setChatPrompt("");
    } catch (err: any) {
      setChatError(err?.response?.data?.detail ?? "Could not generate a chart from that prompt.");
    } finally {
      setChatPending(false);
    }
  }

  function addWidget() {
    if (!dataset) return;
    const widgetId = `custom-widget-${customWidgets.length + 1}`;
    const numericColumns = dataset.columns_schema.filter((c) => c.dtype === "numeric").map((c) => c.name);
    const defaultColumn = numericColumns[0] ?? dataset.columns_schema[0]?.name;
    const defaultX = newWidgetType === "line"
      ? dataset.columns_schema.find((c) => c.dtype === "datetime")?.name ?? numericColumns[0] ?? dataset.columns_schema[0]?.name
      : numericColumns[0] ?? dataset.columns_schema[0]?.name;
    const defaultY = numericColumns[0] ?? dataset.columns_schema[0]?.name;
    const defaultTableColumns = dataset.columns_schema.slice(0, 3).map((c) => c.name);
    const patch = {
      chart: newWidgetType,
      title: `${newWidgetType.toUpperCase()} widget`,
      column: newWidgetType === "table" ? undefined : defaultColumn,
      x: newWidgetType === "line" ? defaultX : undefined,
      y: newWidgetType === "line" ? defaultY : undefined,
      columns: newWidgetType === "table" ? defaultTableColumns : undefined,
      deleted: false,
    };
    updateWidget(dashboardKey, widgetId, patch);
    setCustomWidgets((prev) => [
      ...prev,
      {
        chart: newWidgetType,
        title: `${newWidgetType.toUpperCase()} widget`,
        column: patch.column,
        x: patch.x,
        y: patch.y,
        columns: patch.columns,
        data: [],
      },
    ]);
    setNewWidgetType("kpi");
  }

  // Phase 11 — Export. One entry point for all five formats, wired to
  // the ExportMenu dropdown. PDF/CSV/Excel/JSON export the widgets'
  // underlying data; PNG screenshots the rendered grid itself.
  async function handleExport(format: string) {
    if (exportingFormat) return;
    setExportingFormat(format);
    try {
      const filenamePrefix = `dashboard-export-${fileKey}`;
      const widgets = visibleWidgets.map(({ widget }) => widget);

      if (format === "pdf") {
        if (!gridRef.current) return;
        await exportElementAsPDF(gridRef.current, filenamePrefix);
        return;
      }
      if (format === "csv") {
        exportWidgetsAsCSV(widgets, filenamePrefix);
        return;
      }
      if (format === "excel") {
        exportWidgetsAsExcel(widgets, filenamePrefix);
        return;
      }
      if (format === "json") {
        exportWidgetsAsJSON(
          widgets,
          {
            fileId: id,
            dashboardName: isSavedMode ? savedDashboard?.name : undefined,
            filters,
          },
          filenamePrefix
        );
        return;
      }
      if (format === "png") {
        if (!gridRef.current) return;
        await exportElementAsPNG(gridRef.current, filenamePrefix);
        return;
      }
    } catch (err) {
      window.alert("Export failed. Please try again.");
      // eslint-disable-next-line no-console
      console.error("Export failed:", err);
    } finally {
      setExportingFormat(null);
    }
  }

  // Phase 13 — a large file still being analyzed in the background has
  if (isProgressError) {
    return (
      <div className="min-h-screen px-6 py-10 max-w-3xl mx-auto flex flex-col items-center justify-center text-center gap-4">
        <h1 className="font-display text-2xl font-semibold text-red-400">
          Unable to connect to backend server
        </h1>
        <p className="text-scimly-muted text-sm bg-scimly-surface border border-scimly-border rounded-lg px-4 py-3 max-w-md">
          {(progressErrorObj as any)?.message || "Network error. Please verify the backend server is running and VITE_API_URL is configured."}
        </p>
        <Link to="/upload" className="text-scimly-primary text-sm hover:underline">
          ← Back to Upload
        </Link>
      </div>
    );
  }

  // Phase 13 — a file navigated to directly (bookmark, back button, a
  if (isProcessingBlocked) {
    const failed = processingStatus?.status === "failed";
    return (
      <div className="min-h-screen px-6 py-10 max-w-3xl mx-auto flex flex-col items-center justify-center text-center gap-4">
        <h1 className="font-display text-2xl font-semibold">
          {failed ? "Analysis failed" : "Processing your file…"}
        </h1>
        {!failed && (
          <>
            <div className="w-full max-w-sm h-2 bg-scimly-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-scimly-accent transition-all"
                style={{ width: `${processingStatus?.progress ?? 0}%` }}
              />
            </div>
            <p className="text-scimly-muted text-sm">
              {processingStatus?.message ?? "Checking file status…"}
            </p>
          </>
        )}
        {failed && (
          <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/30 rounded-lg px-4 py-3">
            {processingStatus?.message ?? "Background analysis failed for this file."}
          </p>
        )}
        <Link to="/upload" className="text-scimly-primary text-sm hover:underline">
          ← Back to Upload
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 py-10 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8 flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold">
            {isSavedMode ? savedDashboard?.name ?? "Loading…" : "Dashboard"}
          </h1>
          <p className="text-scimly-muted text-sm">
            {editMode
              ? "Drag to move, drag the corner to resize"
              : isSavedMode
              ? "Saved dashboard"
              : "Auto-generated from your dataset"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {editMode && (
            <>
              <select
                value={newWidgetType}
                onChange={(e) => setNewWidgetType(e.target.value as "kpi" | "line" | "pie" | "bar" | "table")}
                className="bg-scimly-surface border border-scimly-border rounded px-2 py-1 text-sm text-scimly-text"
              >
                <option value="kpi">KPI</option>
                <option value="line">Line</option>
                <option value="pie">Pie</option>
                <option value="bar">Bar</option>
                <option value="table">Table</option>
              </select>
              <button
                onClick={addWidget}
                className="text-sm px-3 py-1.5 rounded-lg border border-scimly-primary text-scimly-primary"
              >
                Add widget
              </button>
              <button
                onClick={() => resetDashboard(dashboardKey)}
                className="text-scimly-muted text-sm hover:text-red-400"
              >
                Reset changes
              </button>
              <button
                onClick={() => resetLayout(dashboardKey)}
                className="text-scimly-muted text-sm hover:text-red-400"
              >
                Reset layout
              </button>
            </>
          )}
          {isSavedMode ? (
            <>
              <button
                onClick={handleSave}
                disabled={updateMutation.isPending}
                className="text-sm px-3 py-1.5 rounded-lg bg-scimly-primary text-scimly-bg hover:scale-[1.01] active:scale-[0.99] font-medium disabled:opacity-50"
              >
                {updateMutation.isPending ? "Saving…" : saveState === "saved" ? "Saved ✓" : "Save Changes"}
              </button>
              <button
                onClick={handleSaveAs}
                disabled={createMutation.isPending}
                className="text-sm px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-muted hover:text-scimly-text disabled:opacity-50"
              >
                {createMutation.isPending ? "Saving…" : "Save Copy as…"}
              </button>
              <Link
                to={`/enterprise?tab=sharing&dashboardId=${savedDashboard?.id}`}
                className="text-sm px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-muted hover:text-scimly-text"
              >
                Share
              </Link>
            </>
          ) : (
            <button
              onClick={handleSaveAs}
              disabled={createMutation.isPending}
              className="text-sm px-3.5 py-1.5 rounded-lg bg-scimly-primary text-scimly-bg hover:scale-[1.01] active:scale-[0.99] font-semibold disabled:opacity-50 shadow-lg shadow-scimly-primary/10"
            >
              {createMutation.isPending ? "Saving…" : "Save Dashboard"}
            </button>
          )}
          <ExportMenu onExport={handleExport} busy={exportingFormat} />
          <button
            onClick={toggleEditMode}
            className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${
              editMode
                ? "bg-scimly-primary/10 border-scimly-primary text-scimly-primary"
                : "border-scimly-border text-scimly-muted hover:text-scimly-text"
            }`}
          >
            {editMode ? "Done editing" : "Edit dashboard"}
          </button>
          <Link to="/dashboards" className="text-scimly-muted text-sm hover:text-scimly-text hover:underline">
            My Dashboards
          </Link>
          <Link to="/upload" className="text-scimly-primary text-sm hover:underline">
            ← Back to Upload
          </Link>
          <AuthStatus />
        </div>
      </div>

      {filterOptions && (
        <FilterBar options={filterOptions} filters={filters} onChange={setFilters} />
      )}

      {dataset && (
        <div className="mb-6 rounded-xl border border-scimly-border bg-scimly-surface/70 p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <div className="flex-1">
              <label className="text-sm font-medium text-scimly-text">Ask Scimly Insight</label>
              <p className="text-xs text-scimly-muted mt-1">
                Try prompts like “Show monthly revenue”, “Top customers”, or “Best products”.
              </p>
              <input
                value={chatPrompt}
                onChange={(event) => setChatPrompt(event.target.value)}
                placeholder="Show monthly revenue"
                className="mt-2 w-full rounded-lg border border-scimly-border bg-scimly-background px-3 py-2 text-sm text-scimly-text outline-none focus:border-scimly-primary"
              />
            </div>
            <button
              onClick={handleAskScimly}
              disabled={chatPending || !chatPrompt.trim()}
              className="rounded-lg border border-scimly-primary bg-scimly-primary px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {chatPending ? "Generating…" : "Generate chart"}
            </button>
          </div>
          {chatError && (
            <p className="mt-3 text-sm text-red-400">{chatError}</p>
          )}
        </div>
      )}

      {!isSavedMode && autoDashboard?.moreWidgets && autoDashboard.moreWidgets.length > 0 && (
        <div className="mb-6 rounded-xl border border-scimly-border bg-scimly-surface/70 p-4">
          <p className="text-sm font-medium text-scimly-text">
            More charts available ({autoDashboard.moreWidgets.length})
          </p>
          <p className="text-xs text-scimly-muted mt-1 mb-3">
            The dashboard opens with just the most important charts. Add any of these too.
          </p>
          <div className="flex flex-wrap gap-2">
            {autoDashboard.moreWidgets.map((widget: DashboardWidget, i: number) => (
              <button
                key={`more-widget-${i}-${widget.title}`}
                onClick={() => setCustomWidgets((current) => [...current, widget])}
                className="text-sm px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-text hover:border-scimly-primary hover:text-scimly-primary"
              >
                + {widget.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {isLoading && <p className="text-scimly-muted">Building your dashboard…</p>}

      {isError && (
        <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/30 rounded-lg px-4 py-3">
          {(error as any)?.response?.data?.detail ??
            "Couldn't load this dashboard. Make sure the file was analyzed first."}
        </p>
      )}

      {data && data.widgets.length === 0 && (
        <p className="text-scimly-muted">
          No charts could be recommended for this dataset yet.
        </p>
      )}

      {data && dataset && visibleWidgets.length > 0 && (
        <div ref={gridRef} className="relative w-full" style={{ minHeight: `${Math.max(300, ((Math.max(0, ...layout.map((item) => item.y + item.h)) + 1) * ROW_HEIGHT) + 40)}px` }}>
          {visibleWidgets.map(({ id: widgetId, widget }) => {
            const item = layout.find((entry) => entry.i === widgetId) ?? { i: widgetId, x: 0, y: 0, w: 3, h: 4 };
            const effectiveCols = gridWidth < 768 ? 1 : GRID_COLS;
            const cellWidth = gridWidth / effectiveCols;
            const displayWidth = Math.min(item.w, effectiveCols);
            const displayX = effectiveCols === 1 ? 0 : item.x;
            return (
              <div
                key={widgetId}
                className="absolute overflow-hidden rounded-xl border border-scimly-border bg-scimly-surface/70"
                style={{
                  left: `${displayX * cellWidth}px`,
                  top: `${item.y * ROW_HEIGHT}px`,
                  width: `${displayWidth * cellWidth - 16}px`,
                  height: `${item.h * ROW_HEIGHT - 16}px`,
                }}
              >
                <EditableWidget
                  fileId={id}
                  storageKey={dashboardKey}
                  widgetId={widgetId}
                  widget={widget}
                  schema={dataset.columns_schema}
                  filters={filters}
                  onStartDrag={startDrag}
                  onStartResize={startResize}
                  onCycleSize={cycleWidgetSize}
                />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
