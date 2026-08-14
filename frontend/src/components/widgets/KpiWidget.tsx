interface KpiWidgetProps {
  title: string;
  value: number | string;
  accentColor?: string;
}

export default function KpiWidget({ title, value, accentColor = "#5B8DEF" }: KpiWidgetProps) {
  return (
    <div className="h-full rounded-xl border border-scimly-border bg-scimly-surface p-4 flex flex-col justify-between">
      <div className="text-sm text-scimly-muted">{title}</div>
      <div className="text-3xl font-semibold" style={{ color: accentColor }}>
        {value}
      </div>
    </div>
  );
}
