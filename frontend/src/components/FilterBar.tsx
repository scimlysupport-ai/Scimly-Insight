import { useState } from "react";
import type {
  CategoricalFilterOption,
  DashboardFilters,
  FilterOptionsResponse,
} from "../services/datasetService";
import { hasActiveFilters } from "../services/datasetService";

interface FilterBarProps {
  options: FilterOptionsResponse;
  filters: DashboardFilters;
  onChange: (next: DashboardFilters) => void;
}

function CategoricalDropdown({
  option,
  selected,
  onChange,
}: {
  option: CategoricalFilterOption;
  selected: string[];
  onChange: (values: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const { column, options: allOptions, type } = option;
  const isTags = type === "tags";

  function toggleValue(value: string) {
    const next = selected.includes(value)
      ? selected.filter((v) => v !== value)
      : [...selected, value];
    onChange(next);
  }

  const label =
    selected.length === 0
      ? column
      : selected.length === 1
      ? `${column}: ${selected[0]}`
      : `${column}: ${selected.length} selected`;

  return (
    <div
      className="relative"
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) setOpen(false);
      }}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${
          selected.length > 0
            ? "border-scimly-primary text-scimly-primary bg-scimly-primary/10"
            : "border-scimly-border text-scimly-muted hover:text-scimly-text"
        }`}
        title={isTags ? "Matches rows containing any selected tag" : undefined}
      >
        {label} <span className="text-xs ml-0.5">▾</span>
      </button>

      {open && (
        <div className="absolute z-30 mt-1 w-60 max-h-64 overflow-auto bg-scimly-surface border border-scimly-border rounded-lg shadow-lg py-1">
          {isTags && (
            <div className="px-3 py-1 text-[10px] uppercase tracking-wide text-scimly-muted border-b border-scimly-border mb-1">
              Matches any selected tag
            </div>
          )}
          {allOptions.map((value) => (
            <label
              key={value}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-scimly-text hover:bg-scimly-bg cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selected.includes(value)}
                onChange={() => toggleValue(value)}
                className="accent-scimly-primary"
              />
              <span className="truncate">{value}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export default function FilterBar({ options, filters, onChange }: FilterBarProps) {
  const noOptions = options.categorical.length === 0 && options.date_ranges.length === 0;
  if (noOptions) return null;

  function setCategorical(column: string, values: string[]) {
    onChange({
      ...filters,
      categorical: { ...filters.categorical, [column]: values },
    });
  }

  function setDateRange(column: string, patch: { start?: string; end?: string }) {
    onChange({
      ...filters,
      date_ranges: {
        ...filters.date_ranges,
        [column]: { ...filters.date_ranges[column], ...patch },
      },
    });
  }

  function clearAll() {
    onChange({ categorical: {}, date_ranges: {} });
  }

  const active = hasActiveFilters(filters);

  return (
    <div className="mb-6 flex flex-wrap items-center gap-2 bg-scimly-surface/50 border border-scimly-border rounded-xl px-3 py-2.5">
      <span className="text-scimly-muted text-xs uppercase tracking-wide mr-1">Filters</span>

      {options.categorical.map((option) => (
        <CategoricalDropdown
          key={option.column}
          option={option}
          selected={filters.categorical[option.column] ?? []}
          onChange={(values) => setCategorical(option.column, values)}
        />
      ))}

      {options.date_ranges.map(({ column, min, max }) => (
        <div
          key={column}
          className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-scimly-border text-scimly-muted"
        >
          <span className="text-xs">{column}</span>
          <input
            type="date"
            min={min}
            max={max}
            value={filters.date_ranges[column]?.start ?? ""}
            onChange={(e) => setDateRange(column, { start: e.target.value || undefined })}
            className="bg-transparent text-scimly-text text-xs w-[110px] outline-none"
          />
          <span className="text-xs">–</span>
          <input
            type="date"
            min={min}
            max={max}
            value={filters.date_ranges[column]?.end ?? ""}
            onChange={(e) => setDateRange(column, { end: e.target.value || undefined })}
            className="bg-transparent text-scimly-text text-xs w-[110px] outline-none"
          />
        </div>
      ))}

      {active && (
        <button
          type="button"
          onClick={clearAll}
          className="text-xs px-2.5 py-1.5 rounded-lg text-scimly-muted hover:text-red-400 ml-auto"
        >
          Clear all filters
        </button>
      )}
    </div>
  );
}
