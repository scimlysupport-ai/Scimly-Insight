import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ChartRenderer from "./ChartRenderer";
import { getWidgetDefinition } from "./widgetRegistry";
import { useDashboardEditStore } from "../store/useDashboardEditStore";
import { fetchChartPreview } from "../services/datasetService";
import type { DashboardWidget, ColumnSchema, DashboardFilters } from "../services/datasetService";

interface EditableWidgetProps {
  fileId: number;
  // Phase 10 — key used for edit-store overrides (title/chart/color
  // etc). Defaults to fileId when omitted, but a saved dashboard passes
  // its own key (e.g. "saved-12") so its edits don't collide with the
  // unsaved auto dashboard's edits for the same file.
  storageKey?: string;
  widgetId: string;
  widget: DashboardWidget;
  schema: ColumnSchema[];
  filters?: DashboardFilters;
  onStartDrag?: (widgetId: string, event: React.MouseEvent<HTMLElement>) => void;
  onStartResize?: (widgetId: string, event: React.MouseEvent<HTMLElement>) => void;
  onCycleSize?: (widgetId: string) => void;
}

const CHART_TYPES: DashboardWidget["chart"][] = ["kpi", "line", "pie", "bar", "table"];
const COLOR_SWATCHES = ["#5B8DEF", "#22D3AA", "#F5A623", "#E85D75", "#9B7EDE", "#4FC3E8"];

function columnsOfType(schema: ColumnSchema[], types: string[]): ColumnSchema[] {
  const matches = schema.filter((c) => types.includes(c.dtype));
  return matches.length > 0 ? matches : schema; // fall back to all columns if none match
}

export default function EditableWidget({ fileId, storageKey, widgetId, widget, schema, filters, onStartDrag, onStartResize, onCycleSize }: EditableWidgetProps) {
  const key = storageKey ?? String(fileId);
  const editMode = useDashboardEditStore((s) => s.editMode);
  const override = useDashboardEditStore((s) => s.overrides[key]?.[widgetId]);
  const updateWidget = useDashboardEditStore((s) => s.updateWidget);
  const deleteWidget = useDashboardEditStore((s) => s.deleteWidget);

  const [isRenaming, setIsRenaming] = useState(false);
  const [draftTitle, setDraftTitle] = useState(override?.title ?? widget.title);

  const effectiveChart = override?.chart ?? widget.chart;
  const effectiveColumn = override?.column ?? widget.column;
  const effectiveX = override?.x ?? widget.x;
  const effectiveY = override?.y ?? widget.y;
  const effectiveTitle = override?.title ?? widget.title;

  const structuralChanged =
    effectiveChart !== widget.chart ||
    effectiveColumn !== widget.column ||
    effectiveX !== widget.x ||
    effectiveY !== widget.y ||
    (override?.columns ?? widget.columns)?.join("|") !== (widget.columns ?? []).join("|");

  const previewRequest = {
    chart: effectiveChart,
    column: effectiveColumn,
    x: effectiveX,
    y: effectiveY,
    columns: (override?.columns ?? widget.columns) ?? undefined,
    filters,
  };

  const { data: preview, isFetching } = useQuery({
    queryKey: [
      "chart-preview",
      fileId,
      effectiveChart,
      effectiveColumn,
      effectiveX,
      effectiveY,
      previewRequest.columns?.join("|"),
      filters,
    ],
    queryFn: () => fetchChartPreview(fileId, previewRequest),
    enabled: structuralChanged,
    retry: false,
  });

  const displayWidget: DashboardWidget = {
    chart: effectiveChart,
    title: effectiveTitle,
    column: effectiveColumn,
    x: effectiveX,
    y: effectiveY,
    columns: previewRequest.columns,
    data: structuralChanged ? preview?.data ?? widget.data : widget.data,
  };

  function patch(fields: Parameters<typeof updateWidget>[2]) {
    updateWidget(key, widgetId, fields);
  }

  const columnOptions = columnsOfType(schema, getWidgetDefinition(effectiveChart)?.columnTypes ?? []);
  const numericOptions = columnsOfType(schema, ["numeric"]);

  return (
    <div
      className="relative group h-full w-full flex flex-col overflow-hidden"
      onMouseDown={(event) => {
        if (!editMode) return;
        const target = event.target as HTMLElement;
        if (target.closest("button, select, input, .no-drag")) return;
        onStartDrag?.(widgetId, event);
      }}
    >
      {editMode && (
        <div className="shrink-0 mb-1 flex flex-wrap items-center gap-1.5 bg-scimly-bg/90 border border-scimly-border rounded-lg px-2 py-1 text-[11px] cursor-default max-h-10 overflow-hidden">
          <button
            className="drag-handle cursor-grab active:cursor-grabbing text-scimly-muted hover:text-scimly-text"
            title="Drag widget"
            type="button"
            onMouseDown={(event) => {
              event.stopPropagation();
              onStartDrag?.(widgetId, event);
            }}
          >
            ⋮⋮
          </button>
          {isRenaming ? (
            <input
              autoFocus
              value={draftTitle}
              onChange={(e) => setDraftTitle(e.target.value)}
              onBlur={() => {
                patch({ title: draftTitle });
                setIsRenaming(false);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  patch({ title: draftTitle });
                  setIsRenaming(false);
                }
              }}
              className="no-drag bg-scimly-surface border border-scimly-border rounded px-2 py-1 text-scimly-text text-xs w-32"
            />
          ) : (
            <button
              onClick={() => setIsRenaming(true)}
              className="no-drag text-scimly-muted hover:text-scimly-text"
              title="Rename"
            >
              ✏️ Rename
            </button>
          )}

          <select
            value={effectiveChart}
            onChange={(e) => {
              const newChart = e.target.value as DashboardWidget["chart"];
              if (newChart === "line") {
                const dateCol = schema.find((c) => c.dtype === "datetime")?.name ?? schema[0]?.name;
                const numCol = columnsOfType(schema, ["numeric"])[0]?.name;
                patch({ chart: newChart, x: dateCol, y: numCol, column: undefined, columns: undefined });
              } else if (newChart === "table") {
                const validCols = columnsOfType(schema, getWidgetDefinition(newChart)?.columnTypes ?? []);
                patch({
                  chart: newChart,
                  column: undefined,
                  x: undefined,
                  y: undefined,
                  columns: validCols.map((c) => c.name),
                });
              } else {
                const validCols = columnsOfType(schema, getWidgetDefinition(newChart)?.columnTypes ?? []);
                patch({
                  chart: newChart,
                  column: validCols[0]?.name,
                  x: undefined,
                  y: undefined,
                  columns: undefined,
                });
              }
            }}
            className="no-drag bg-scimly-surface border border-scimly-border rounded px-1.5 py-1 text-scimly-text"
          >
            {CHART_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.toUpperCase()}
              </option>
            ))}
          </select>

          {effectiveChart === "line" ? (
            <>
              <select
                value={effectiveX ?? ""}
                onChange={(e) => patch({ x: e.target.value })}
                className="no-drag bg-scimly-surface border border-scimly-border rounded px-1.5 py-1 text-scimly-text"
              >
                <option value="" disabled>X axis</option>
                {schema.map((c) => (
                  <option key={c.name} value={c.name}>{c.name}</option>
                ))}
              </select>
              <select
                value={effectiveY ?? ""}
                onChange={(e) => patch({ y: e.target.value })}
                className="no-drag bg-scimly-surface border border-scimly-border rounded px-1.5 py-1 text-scimly-text"
              >
                <option value="" disabled>Y axis</option>
                {numericOptions.map((c) => (
                  <option key={c.name} value={c.name}>{c.name}</option>
                ))}
              </select>
            </>
          ) : (
            <select
              value={effectiveColumn ?? ""}
              onChange={(e) => patch({ column: e.target.value })}
              className="no-drag bg-scimly-surface border border-scimly-border rounded px-1.5 py-1 text-scimly-text"
            >
              <option value="" disabled>Column</option>
              {columnOptions.map((c) => (
                <option key={c.name} value={c.name}>{c.name}</option>
              ))}
            </select>
          )}

          <div className="flex items-center gap-1">
            {COLOR_SWATCHES.map((color) => (
              <button
                key={color}
                onClick={() => patch({ color })}
                className="no-drag w-4 h-4 rounded-full border border-scimly-border"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>

          <button
            type="button"
            onClick={() => onCycleSize?.(widgetId)}
            className="no-drag rounded border border-scimly-border px-1.5 py-0.5 text-[11px] text-scimly-muted hover:text-scimly-text"
            title="Cycle widget size"
          >
            ↔
          </button>

          <button
            onClick={() => deleteWidget(key, widgetId)}
            className="no-drag text-red-400 hover:text-red-300 ml-auto"
            title="Delete widget"
          >
            🗑
          </button>
        </div>
      )}

      {editMode && (
        <div
          className="absolute bottom-1 right-1 z-20 h-5 w-5 cursor-se-resize rounded-tl-md border-l border-t border-scimly-border bg-scimly-surface/90"
          title="Resize widget"
          onMouseDown={(event) => onStartResize?.(widgetId, event)}
        />
      )}

      {isFetching && structuralChanged ? (
        <div className="flex-1 min-h-0 overflow-hidden rounded-xl border border-scimly-border bg-scimly-surface p-3 flex items-center justify-center">
          <span className="text-scimly-muted text-sm">Updating chart…</span>
        </div>
      ) : (
        <div className="flex-1 min-h-0 overflow-hidden">
          <ChartRenderer widget={displayWidget} accentColor={override?.color} />
        </div>
      )}
    </div>
  );
}
