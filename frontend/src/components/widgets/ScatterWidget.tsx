import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ScatterWidgetProps {
  title: string;
  data: { x: number; y: number }[];
  accentColor?: string;
}

export default function ScatterWidget({
  title,
  data,
  accentColor = "#5B8DEF",
}: ScatterWidgetProps) {
  return (
    <div className="h-full rounded-xl border border-scimly-border bg-scimly-surface p-4">
      <div className="mb-3 text-sm font-medium text-scimly-text">{title}</div>
      <div className="h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
            <XAxis type="number" dataKey="x" name="x" />
            <YAxis type="number" dataKey="y" name="y" />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={data} fill={accentColor} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
