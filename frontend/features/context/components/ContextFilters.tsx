import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/cn";
import type { SourceTypeFilter } from "../utils/sourceFilters";

interface ContextFiltersProps {
  query: string;
  onQueryChange: (query: string) => void;
  typeFilter: SourceTypeFilter;
  onTypeFilterChange: (filter: SourceTypeFilter) => void;
}

const TYPE_OPTIONS: { value: SourceTypeFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "files", label: "Files" },
  { value: "notes", label: "Notes" },
];

/** Search is live. The two dropdowns are placeholders until pillars and creators exist. */
export function ContextFilters({ query, onQueryChange, typeFilter, onTypeFilterChange }: ContextFiltersProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-3">
        <PlaceholderSelect label="All pillars" />
        <PlaceholderSelect label="Created by" />
      </div>
      <div role="group" aria-label="Filter by source type" className="grid grid-cols-3 gap-1 rounded-control bg-page p-1">
        {TYPE_OPTIONS.map((option) => {
          const selected = typeFilter === option.value;
          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => onTypeFilterChange(option.value)}
              className={cn(
                "h-7 rounded-control text-body-small focus-visible:outline-2 focus-visible:outline-border-brand-strong",
                selected ? "bg-surface font-semibold text-fg" : "text-fg-muted hover:text-fg",
              )}
            >
              {option.label}
            </button>
          );
        })}
      </div>
      <Input
        type="search"
        name="search"
        aria-label="Search sources"
        placeholder="Search sources and notes"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
      />
    </div>
  );
}

function PlaceholderSelect({ label }: { label: string }) {
  return (
    <select
      disabled
      aria-label={label}
      title="Yet to be done"
      className="h-9 rounded-control border border-border bg-surface-disabled px-3 text-body-small text-fg-disabled"
    >
      <option>{label}</option>
    </select>
  );
}
