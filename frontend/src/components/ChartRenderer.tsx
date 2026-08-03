import { getWidgetDefinition } from "./widgetRegistry";
import type { DashboardWidget } from "../services/datasetService";

interface ChartRendererProps {
  widget: DashboardWidget;
  accentColor?: string;
}

function Placeholder({ message }: { message: string }) {
  return (
    <div className="bg-scimly-surface border border-scimly-border rounded-xl p-5 h-full flex items-center justify-center">
      <span className="text-scimly-muted text-sm">{message}</span>
    </div>
  );
}

/**
 * Purely a lookup into WIDGET_REGISTRY — this file never needs to change
 * when a new chart type is added. It reads the widget's `chart` field,
 * finds the matching definition, and renders it, or shows a clear
 * fallback if the type is unsupported or the data is empty.
 */
export default function ChartRenderer({ widget, accentColor }: ChartRendererProps) {
  const definition = getWidgetDefinition(widget.chart);

  if (!definition) {
    return <Placeholder message={`Unsupported chart type: ${widget.chart}`} />;
  }

  if (definition.isEmpty(widget.data)) {
    return <Placeholder message="Not enough data to show this chart" />;
  }

  const Component = definition.component;
  return <Component {...definition.mapProps(widget, accentColor)} />;
}
