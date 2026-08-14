interface TableWidgetProps {
  title: string;
  columns: string[];
  rows: Record<string, unknown>[];
  totalRows: number;
  accentColor?: string;
}

export default function TableWidget({ title, columns, rows, totalRows, accentColor = "#5B8DEF" }: TableWidgetProps) {
  return (
    <div className="h-full rounded-xl border border-scimly-border bg-scimly-surface p-3 flex flex-col">
      <div className="mb-2 flex items-center justify-between text-sm font-medium text-scimly-text">
        <span>{title}</span>
        <span className="text-xs text-scimly-muted">{totalRows} rows</span>
      </div>
      <div className="flex-1 min-h-0 overflow-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-scimly-border text-left text-scimly-muted">
              {columns.map((column) => (
                <th key={column} className="px-2 py-1 font-medium">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={`${rowIndex}`} className="border-b border-scimly-border/50 text-scimly-text">
                {columns.map((column) => (
                  <td key={`${rowIndex}-${column}`} className="px-2 py-1 whitespace-nowrap">
                    {row[column] == null ? "—" : String(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-2 text-xs text-scimly-muted" style={{ color: accentColor }}>
        Preview table
      </div>
    </div>
  );
}
