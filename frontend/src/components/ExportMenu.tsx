import { useEffect, useRef, useState } from "react";

export interface ExportOption {
  key: string;
  label: string;
  description: string;
}

const OPTIONS: ExportOption[] = [
  { key: "pdf", label: "PDF", description: "Printable report with tables" },
  { key: "png", label: "PNG", description: "Snapshot image of the dashboard" },
  { key: "csv", label: "CSV", description: "Widget data as plain text" },
  { key: "excel", label: "Excel", description: "Workbook, one sheet per widget" },
  { key: "json", label: "JSON", description: "Raw widget config + data" },
];

interface ExportMenuProps {
  onExport: (format: string) => void;
  busy?: string | null;
}

/**
 * Phase 11 — Export.
 *
 * A small dropdown that replaces the old single "Download PDF" button.
 * Each option calls back into Dashboard.tsx with the chosen format;
 * this component only owns the open/closed UI state.
 */
export default function ExportMenu({ onExport, busy }: ExportMenuProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const isBusy = !!busy;

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={isBusy}
        className="text-sm px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-muted hover:text-scimly-text disabled:opacity-50 flex items-center gap-1.5"
      >
        {isBusy ? `Exporting ${busy!.toUpperCase()}…` : "Export"}
        {!isBusy && <span className="text-xs">▾</span>}
      </button>

      {open && !isBusy && (
        <div className="absolute right-0 mt-1 w-56 bg-scimly-surface border border-scimly-border rounded-lg shadow-lg z-20 overflow-hidden">
          {OPTIONS.map((option) => (
            <button
              key={option.key}
              onClick={() => {
                setOpen(false);
                onExport(option.key);
              }}
              className="w-full text-left px-3 py-2 hover:bg-scimly-border/40 transition-colors"
            >
              <div className="text-sm text-scimly-text">{option.label}</div>
              <div className="text-xs text-scimly-muted">{option.description}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
