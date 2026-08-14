import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface LineWidgetProps {
  title: string;
  data: Array<{ x: string; y: number }>;
  accentColor?: string;
}

export default function LineWidget({ title, data, accentColor = "#5B8DEF" }: LineWidgetProps) {
  return (
    <div className="h-full rounded-xl border border-scimly-border bg-scimly-surface p-3 flex flex-col">
      <div className="mb-2 text-sm font-medium text-scimly-text">{title}</div>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="x" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip />
            <Line type="monotone" dataKey="y" stroke={accentColor} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
