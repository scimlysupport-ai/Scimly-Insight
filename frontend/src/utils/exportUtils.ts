import * as XLSX from "xlsx";
import html2canvas from "html2canvas";
import type { DashboardWidget } from "../services/datasetService";

/**
 * Phase 11 — Export.
 *
 * Every widget's `data` shape is different depending on its chart type
 * (see widgetRegistry.ts), so before we can write it to CSV/Excel we
 * need one shared "table" shape to convert down to. This mirrors the
 * same normalization the PDF export in Dashboard.tsx already does for
 * its text summaries, just producing rows/columns instead of strings.
 */
export interface NormalizedTable {
  title: string;
  columns: string[];
  rows: (string | number)[][];
}

function safeSheetName(name: string, used: Set<string>): string {
  // Excel sheet names: <=31 chars, no []:*?/\\, and must be unique per workbook.
  let base = (name || "Widget").replace(/[\[\]:*?/\\]/g, " ").trim();
  if (!base) base = "Widget";
  base = base.slice(0, 31);
  let candidate = base;
  let suffix = 2;
  while (used.has(candidate.toLowerCase())) {
    const tail = ` (${suffix})`;
    candidate = base.slice(0, 31 - tail.length) + tail;
    suffix += 1;
  }
  used.add(candidate.toLowerCase());
  return candidate;
}

export function normalizeWidget(widget: DashboardWidget): NormalizedTable {
  const title = widget.title ?? "Untitled widget";

  if (widget.chart === "table") {
    const tableData = (widget.data as { columns?: string[]; rows?: Record<string, unknown>[] } | undefined) ?? {};
    const columns = tableData.columns ?? [];
    const rows = (tableData.rows ?? []).map((row) => columns.map((col) => row?.[col] as string | number));
    return { title, columns, rows };
  }

  if (widget.chart === "kpi") {
    const value = (widget.data as { value?: number } | undefined)?.value;
    return {
      title,
      columns: ["Metric", "Value"],
      rows: [[widget.column ?? title, value ?? ""]],
    };
  }

  if (widget.chart === "line") {
    const points = (widget.data as { x: string; y: number }[] | undefined) ?? [];
    return {
      title,
      columns: [widget.x ?? "x", widget.y ?? "y"],
      rows: points.map((p) => [p.x, p.y]),
    };
  }

  // pie / bar share the same { name, value } shape
  const points = (widget.data as { name: string; value: number }[] | undefined) ?? [];
  return {
    title,
    columns: [widget.column ?? "Category", "Value"],
    rows: points.map((p) => [p.name, p.value]),
  };
}

function csvEscape(value: unknown): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function downloadBlob(content: BlobPart, mimeType: string, filename: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

/** One CSV file, with each widget written as its own labeled section. */
export function exportWidgetsAsCSV(widgets: DashboardWidget[], filenamePrefix: string) {
  const tables = widgets.map(normalizeWidget);
  const lines: string[] = [];

  tables.forEach((table, index) => {
    if (index > 0) lines.push("");
    lines.push(csvEscape(table.title));
    if (table.columns.length === 0) {
      lines.push("No data available");
      return;
    }
    lines.push(table.columns.map(csvEscape).join(","));
    table.rows.forEach((row) => {
      lines.push(row.map(csvEscape).join(","));
    });
  });

  downloadBlob(lines.join("\n"), "text/csv;charset=utf-8;", `${filenamePrefix}.csv`);
}

/** One .xlsx workbook, with one sheet per widget. */
export function exportWidgetsAsExcel(widgets: DashboardWidget[], filenamePrefix: string) {
  const workbook = XLSX.utils.book_new();
  const usedNames = new Set<string>();

  const tables = widgets.map(normalizeWidget);
  if (tables.length === 0) {
    tables.push({ title: "Dashboard", columns: ["No data"], rows: [] });
  }

  tables.forEach((table) => {
    const sheetData = [table.columns, ...table.rows];
    const sheet = XLSX.utils.aoa_to_sheet(sheetData.length ? sheetData : [["No data available"]]);
    XLSX.utils.book_append_sheet(workbook, sheet, safeSheetName(table.title, usedNames));
  });

  XLSX.writeFile(workbook, `${filenamePrefix}.xlsx`);
}

/** Raw JSON snapshot of the dashboard's widgets (config + data). */
export function exportWidgetsAsJSON(
  widgets: DashboardWidget[],
  meta: Record<string, unknown>,
  filenamePrefix: string
) {
  const payload = {
    exportedAt: new Date().toISOString(),
    ...meta,
    widgets,
  };
  downloadBlob(JSON.stringify(payload, null, 2), "application/json", `${filenamePrefix}.json`);
}

/** Screenshots a DOM node (the dashboard grid) and downloads it as a PNG. */
export async function exportElementAsPNG(element: HTMLElement, filenamePrefix: string) {
  const canvas = await html2canvas(element, {
    backgroundColor: "#0b0f19",
    scale: Math.min(2, window.devicePixelRatio || 1.5),
    useCORS: true,
  });

  await new Promise<void>((resolve) => {
    canvas.toBlob((blob) => {
      if (blob) {
        downloadBlob(blob, "image/png", `${filenamePrefix}.png`);
      }
      resolve();
    }, "image/png");
  });
}
