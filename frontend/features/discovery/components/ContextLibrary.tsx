"use client";

import { useRef, useState } from "react";
import type { DiscoveryStats, Pillar, PillarId, Source, SourceStatus } from "../types/discovery.types";
import { badgeClass, buttonClass } from "../utils/class-names";
import { toPercent } from "../utils/discovery-stats";
import { CloseIcon, PlusIcon, SearchIcon } from "./icons";

const BADGE_FOR_STATUS: Record<SourceStatus, string> = {
  Uploaded: badgeClass.grey,
  "Auto-synthesized": badgeClass.brand,
  Processing: badgeClass.warning,
};

const fieldClass =
  "w-full rounded-(--radius-md) border border-(--color-border-default-primary) bg-(--color-bg-default-primary) " +
  "px-(--space-3) py-(--space-2) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) " +
  "leading-(--line-height-body-medium) text-(--color-text-default-primary) hover:border-(--color-border-brand-primary) " +
  "focus-visible:outline-none focus-visible:border-(--color-border-brand-strong)";

const metaClass = "m-0 text-(length:--font-size-caption) leading-(--line-height-caption) text-(--color-text-default-subtle)";

interface ContextLibraryProps {
  pillars: Pillar[];
  stats: DiscoveryStats;
  sources: Source[];
  onAddFiles: (files: File[]) => void;
  onClose: () => void;
}

/** Right-hand panel: progress summary, add buttons, search, filters, sources. */
export function ContextLibrary({ pillars, stats, sources, onAddFiles, onClose }: ContextLibraryProps) {
  const [query, setQuery] = useState("");
  const [pillarFilter, setPillarFilter] = useState<PillarId | "ALL">("ALL");
  const [creatorFilter, setCreatorFilter] = useState("ALL");
  const fileInput = useRef<HTMLInputElement>(null);

  const creators = [...new Set(sources.map((s) => s.createdBy))];

  const visibleSources = sources.filter(
    (s) =>
      s.title.toLowerCase().includes(query.trim().toLowerCase()) &&
      (pillarFilter === "ALL" || s.pillars.includes(pillarFilter)) &&
      (creatorFilter === "ALL" || s.createdBy === creatorFilter),
  );

  return (
    <aside
      id="context-library"
      aria-labelledby="context-library-title"
      className="flex flex-col gap-(--space-4) border-t lg:border-t-0 lg:border-l border-(--color-border-default-disabled) bg-(--color-bg-default-primary) px-(--space-5) py-(--space-6)"
    >
      <div className="flex items-center justify-between">
        <h2 id="context-library-title" className="m-0 text-(length:--font-size-title-medium) leading-(--line-height-title-medium) font-semibold">
          Context library
        </h2>
        <button type="button" onClick={onClose} aria-label="Close context library" className={buttonClass.icon}>
          <CloseIcon />
        </button>
      </div>

      {/* Progress summary */}
      <section
        aria-label="Discovery progress"
        className="flex flex-col gap-(--space-3) rounded-(--radius-lg) border border-(--color-border-default-disabled) p-(--space-4)"
      >
        <p className="m-0 text-(length:--font-size-body-large) leading-(--line-height-body-large) font-semibold">
          Discovery · {stats.percent}% · {stats.verified}/{stats.total} reviewed
        </p>
        <ul className="m-0 flex list-none flex-col gap-(--space-2) p-0">
          {pillars.map((p) => (
            <li
              key={p.id}
              className="grid grid-cols-[var(--space-10)_1fr_auto] items-center gap-(--space-3) text-(length:--font-size-body-small) leading-(--line-height-body-small)"
            >
              <span>{p.shortName}</span>
              <div aria-hidden="true" className="h-(--space-1) overflow-hidden rounded-full bg-(--color-bg-default-disabled)">
                <div className="h-full bg-(--color-primary-default)" style={{ width: `${toPercent(p.verified, p.total)}%` }} />
              </div>
              <span className={metaClass}>{p.verified}/{p.total} reviewed</span>
            </li>
          ))}
        </ul>
        <p className={metaClass}>
          {stats.unresolved} unresolved · {stats.awaitingReview} awaiting review
        </p>
      </section>

      {/* Add buttons */}
      <div className="grid grid-cols-2 gap-(--space-2)">
        <button type="button" onClick={() => fileInput.current?.click()} className={buttonClass.primary}>
          <PlusIcon />
          Add Files
        </button>
        {/* PLACEHOLDER: Add Note has no design or API yet. */}
        <button type="button" className={buttonClass.subtle}>
          <PlusIcon />
          Add Note
        </button>
        <input
          ref={fileInput}
          type="file"
          multiple
          hidden
          accept=".txt,.md,.docx,.pdf,.xlsx,.pptx,image/*"
          onChange={(e) => {
            onAddFiles(Array.from(e.target.files ?? []));
            e.target.value = "";
          }}
        />
      </div>
      <p className={metaClass}>Drop files anywhere in this project, or use Add Files, or add a Note.</p>

      {/* Search */}
      <div className="relative flex items-center">
        <span className="pointer-events-none absolute left-(--space-3) inline-flex text-(--color-icon-secondary)">
          <SearchIcon />
        </span>
        <input
          type="search"
          placeholder="Search sources"
          aria-label="Search sources"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className={`${fieldClass} pl-(--space-10) placeholder:text-(--color-text-default-subtle)`}
        />
      </div>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-(--space-2)">
        <select
          aria-label="Filter by pillar"
          value={pillarFilter}
          onChange={(e) => setPillarFilter(e.target.value as PillarId | "ALL")}
          className={fieldClass}
        >
          <option value="ALL">All pillars</option>
          {pillars.map((p) => (
            <option key={p.id} value={p.id}>{p.shortName}</option>
          ))}
        </select>
        <select
          aria-label="Filter by creator"
          value={creatorFilter}
          onChange={(e) => setCreatorFilter(e.target.value)}
          className={fieldClass}
        >
          <option value="ALL">Created by</option>
          {creators.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* Source list */}
      <div className="flex items-baseline justify-between">
        <h3 className="m-0 text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold">
          Project sources
        </h3>
        <span className={metaClass}>
          {visibleSources.length === sources.length
            ? `${sources.length} total`
            : `${visibleSources.length} of ${sources.length}`}
        </span>
      </div>

      {visibleSources.length === 0 ? (
        <p className={metaClass}>
          {sources.length === 0 ? "No sources yet. Add files to start discovery." : "No sources match these filters."}
        </p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-(--space-4) p-0">
          {visibleSources.map((s) => (
            <li key={s.id} className="flex flex-col items-start gap-(--space-1)">
              <span className="break-words text-(length:--font-size-body-small) leading-(--line-height-body-small) font-medium">
                {s.title}
              </span>
              <span className={BADGE_FOR_STATUS[s.status]}>{s.status}</span>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}