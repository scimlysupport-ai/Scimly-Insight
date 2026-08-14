import type { ComponentType } from "react";
import KpiWidget from "./widgets/KpiWidget";
import LineWidget from "./widgets/LineWidget";
import PieWidget from "./widgets/PieWidget";
import BarWidget from "./widgets/BarWidget";
import ScatterWidget from "./widgets/ScatterWidget";
import TableWidget from "./widgets/TableWidget";
import type { DashboardWidget } from "../services/datasetService";

/**
 * Every supported chart type is registered here exactly once, with:
 *  - component: the React component that draws it
 *  - span: how many grid columns it should occupy on the dashboard
 *  - isEmpty: how to tell if this widget's data has nothing worth showing
 *
 * To support a new chart type in the future (Phase 7+), add one entry
 * here — no other file needs to change.
 */
interface WidgetDefinition {
  component: ComponentType<any>;
  isEmpty: (data: unknown) => boolean;
  mapProps: (widget: DashboardWidget, color?: string) => Record<string, unknown>;
  // Which dataset column types are valid for the primary "column" selector,
  // used to populate the axis dropdowns in edit mode.
  columnTypes: string[];
}

export const WIDGET_REGISTRY: Record<string, WidgetDefinition> = {
  kpi: {
    component: KpiWidget,
    isEmpty: (data) => {
      const value = (data as { value?: number } | undefined)?.value;
      return value === undefined || value === null || Number.isNaN(value);
    },
    mapProps: (widget, color) => ({
      title: widget.title,
      value: (widget.data as { value: number }).value,
      accentColor: color,
    }),
    columnTypes: ["numeric"],
  },
  line: {
    component: LineWidget,
    isEmpty: (data) => !Array.isArray(data) || data.length === 0,
    mapProps: (widget, color) => ({
      title: widget.title,
      data: widget.data as { x: string; y: number }[],
      accentColor: color,
    }),
    columnTypes: ["numeric"],
  },
  pie: {
    component: PieWidget,
    isEmpty: (data) => !Array.isArray(data) || data.length === 0,
    mapProps: (widget, color) => ({
      title: widget.title,
      data: widget.data as { name: string; value: number }[],
      accentColor: color,
    }),
    columnTypes: ["categorical"],
  },
  bar: {
    component: BarWidget,
    isEmpty: (data) => !Array.isArray(data) || data.length === 0,
    mapProps: (widget, color) => ({
      title: widget.title,
      data: widget.data as { name: string; value: number }[],
      accentColor: color,
    }),
    columnTypes: ["numeric"],
  },
  scatter: {
    component: ScatterWidget,
    isEmpty: (data) => !Array.isArray(data) || data.length === 0,
    mapProps: (widget, color) => ({
      title: widget.title,
      data: widget.data as { x: number; y: number }[],
      accentColor: color,
    }),
    columnTypes: ["numeric"],
  },
  table: {
    component: TableWidget,
    isEmpty: (data) => {
      const rows = (data as { rows?: unknown[] } | undefined)?.rows;
      return !Array.isArray(rows) || rows.length === 0;
    },
    mapProps: (widget, color) => {
      const tableData = widget.data as {
        columns: string[];
        rows: Record<string, unknown>[];
        totalRows: number;
      };
      return {
        title: widget.title,
        columns: tableData.columns,
        rows: tableData.rows,
        totalRows: tableData.totalRows,
        accentColor: color,
      };
    },
    // Any column type can end up in the table (that's the point — it's
    // the catch-all for columns a chart can't represent).
    columnTypes: ["text", "categorical", "boolean"],
  },
};

export function getWidgetDefinition(chartType: string): WidgetDefinition | undefined {
  return WIDGET_REGISTRY[chartType];
}