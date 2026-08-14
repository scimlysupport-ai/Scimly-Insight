import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from "recharts";

interface PieWidgetProps {
  title: string;
  data: Array<{ name: string; value: number }>;
  accentColor?: string;
}

const DEFAULT_COLORS = ["#5B8DEF", "#22D3AA", "#F5A623", "#E85D75", "#9B7EDE", "#4FC3E8"];

export default function PieWidget({ title, data, accentColor = "#5B8DEF" }: PieWidgetProps) {
  return (
    <div className="h-full rounded-xl border border-scimly-border bg-scimly-surface p-3 flex flex-col">
      <div className="mb-2 text-sm font-medium text-scimly-text">{title}</div>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              outerRadius="70%"
              paddingAngle={2}
              label={{ fill: '#94a3b8', fontSize: 11 }}
            >
              {data.map((entry, index) => (
                <Cell key={`${entry.name}-${index}`} fill={index === 0 ? accentColor : DEFAULT_COLORS[index % DEFAULT_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend verticalAlign="bottom" height={36} formatter={(value) => <span className="text-[11px] text-scimly-text/80">{value}</span>} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
