import { Input } from "@/components/ui/Input";

interface ContextFiltersProps {
  query: string;
  onQueryChange: (query: string) => void;
}

/** Search is live. The two dropdowns are placeholders until pillars and creators exist. */
export function ContextFilters({ query, onQueryChange }: ContextFiltersProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-3">
        <PlaceholderSelect label="All pillars" />
        <PlaceholderSelect label="Created by" />
      </div>
      <Input
        type="search"
        name="search"
        aria-label="Search sources"
        placeholder="Search sources"
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