"use client";

import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { PILLAR_LABELS, SOURCE_ORIGINS } from "../constants";
import { useSourceFilters } from "../hooks/useSourceFilters";
import type { ContextSource, PillarId, SourceOrigin } from "../types/contextLibrary";
import { SourceListItem } from "./SourceListItem";

export function SourceBrowser({ sources }: { sources: ContextSource[] }) {
  const { query, setQuery, pillar, setPillar, origin, setOrigin, filteredSources } =
    useSourceFilters(sources);

  return (
    <section aria-labelledby="project-sources-heading" className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <h3 id="project-sources-heading" className="text-body-large font-semibold text-fg">
          Project sources
        </h3>
        <span className="text-body-medium text-fg-muted">{sources.length} total</span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Select
          aria-label="Filter by pillar"
          value={pillar}
          onChange={(event) => setPillar(event.target.value as PillarId | "all")}
        >
          <option value="all">All pillars</option>
          {Object.entries(PILLAR_LABELS).map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </Select>
        <Select
          aria-label="Filter by creator"
          value={origin}
          onChange={(event) => setOrigin(event.target.value as SourceOrigin | "all")}
        >
          <option value="all">Created by</option>
          {Object.entries(SOURCE_ORIGINS).map(([id, { label }]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </Select>
      </div>

      <Input
        type="search"
        aria-label="Search sources"
        placeholder="Search sources"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />

      {filteredSources.length > 0 ? (
        <ul className="flex flex-col gap-4">
          {filteredSources.map((source) => (
            <SourceListItem key={source.id} source={source} />
          ))}
        </ul>
      ) : (
        <p className="text-body-small text-fg-muted">No sources match your filters.</p>
      )}
    </section>
  );
}