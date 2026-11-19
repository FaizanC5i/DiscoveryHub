"use client";

import { useMemo, useRef, useState } from "react";
import { PlusIcon } from "@/components/icons";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Select } from "@/components/ui/Select";
import type { DiscoveryStats, Pillar, PillarId } from "@/features/discovery/types/discovery.types";
import type { RelevantSource } from "../types/pillar-discovery.types";

const ACCEPT = ".txt,.md,.docx,.pdf,.xlsx,.pptx,image/*";

interface PillarContextLibraryProps {
  pillarId: PillarId;
  pillarName: string; // "User Discovery"
  pillars: Pillar[];
  stats: DiscoveryStats;
  sources: RelevantSource[];
  onAddFiles: (files: File[]) => Promise<void>;
}

/** "User + Tech" from ["USER", "TECH"]. */
function pillarLabel(ids: PillarId[], pillars: Pillar[]): string {
  return ids.map((id) => pillars.find((p) => p.id === id)?.shortName ?? id).join(" + ");
}

/** Right-hand panel on a pillar page: overall progress, add buttons, and the sources linked to this pillar. */
export function PillarContextLibrary({
  pillarId,
  pillarName,
  pillars,
  stats,
  sources,
  onAddFiles,
}: PillarContextLibraryProps) {
  const [query, setQuery] = useState("");
  const [pillarFilter, setPillarFilter] = useState<PillarId | "ALL">(pillarId);
  const [creatorFilter, setCreatorFilter] = useState("ALL");
  const fileInput = useRef<HTMLInputElement>(null);

  const creators = useMemo(() => [...new Set(sources.map((s) => s.createdBy))], [sources]);
  const visible = sources.filter(
    (s) =>
      s.title.toLowerCase().includes(query.trim().toLowerCase()) &&
      (pillarFilter === "ALL" || s.pillars.includes(pillarFilter)) &&
      (creatorFilter === "ALL" || s.createdBy === creatorFilter),
  );

  return (
    <aside
      id="pillar-context-library"
      aria-labelledby="pillar-context-library-title"
      className="flex flex-col gap-5 border-t border-border-disabled bg-surface px-6 py-6 lg:w-85 lg:border-t-0 lg:border-l"
    >
      <h2 id="pillar-context-library-title" className="text-title-medium font-medium text-fg">
        Context library
      </h2>

      <section aria-label="Discovery progress" className="flex flex-col gap-3 rounded-card border border-border-disabled p-4">
        <p className="text-body-large font-semibold text-fg">
          Discovery · {stats.percent}% · {stats.verified}/{stats.total} reviewed
        </p>
        <ul className="flex flex-col gap-2">
          {pillars.map((p) => (
            <li key={p.id} className="grid grid-cols-[3rem_1fr_auto] items-center gap-3 text-body-medium text-fg">
              <span>{p.shortName}</span>
              <ProgressBar value={p.total === 0 ? 0 : Math.round((p.verified / p.total) * 100)} label={`${p.name} reviewed`} />
              <span className="text-caption text-fg-muted">
                {p.verified}/{p.total} reviewed
              </span>
            </li>
          ))}
        </ul>
        <p className="text-caption text-fg-muted">
          {stats.unresolved} unresolved · {stats.awaitingReview} awaiting review
        </p>
      </section>

      <div className="grid grid-cols-2 gap-2">
        <Button size="sm" onClick={() => fileInput.current?.click()}>
          <PlusIcon className="size-4" />
          Add Files
        </Button>
        {/* PLACEHOLDER: notes are added from the Overview's context library for now. */}
        <Button variant="outline" size="sm">
          <PlusIcon className="size-4" />
          Add Note
        </Button>
        <input
          ref={fileInput}
          type="file"
          multiple
          hidden
          accept={ACCEPT}
          aria-label="Add files to the context library"
          onChange={(e) => {
            const files = Array.from(e.target.files ?? []);
            e.target.value = "";
            void onAddFiles(files);
          }}
        />
      </div>
      <p className="text-caption text-fg-muted">Drop files anywhere in this project, or use Add files, or add a Note</p>

      <Input
        type="search"
        placeholder="Search sources"
        aria-label="Search sources"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="text-body-medium"
      />

      <div className="grid grid-cols-2 gap-2">
        <Select
          aria-label="Filter by pillar"
          value={pillarFilter}
          onChange={(e) => setPillarFilter(e.target.value as PillarId | "ALL")}
        >
          <option value="ALL">All pillars</option>
          {pillars.map((p) => (
            <option key={p.id} value={p.id}>
              {p.shortName}
            </option>
          ))}
        </Select>
        <Select aria-label="Filter by creator" value={creatorFilter} onChange={(e) => setCreatorFilter(e.target.value)}>
          <option value="ALL">Created by</option>
          {creators.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </Select>
      </div>

      <section aria-labelledby="relevant-sources-title" className="flex flex-col gap-4">
        <div className="flex items-baseline justify-between gap-3">
          <h3 id="relevant-sources-title" className="text-body-large font-medium text-fg">
            Relevant to {pillarName}
          </h3>
          <span className="text-body-medium text-fg-muted">{visible.length}</span>
        </div>

        {visible.length === 0 ? (
          <p className="text-body-small text-fg-muted">
            {sources.length === 0 ? "No sources linked to this area yet." : "No sources match these filters."}
          </p>
        ) : (
          <ul className="flex flex-col gap-4">
            {visible.map((source) => (
              <li key={source.id} className="flex flex-col items-start gap-1">
                <span className="break-all text-body-medium font-semibold text-fg">{source.title}</span>
                {source.status === "Auto-synthesized" ? (
                  <Badge tone="brand" className="rounded-full px-3">
                    Auto-synthesized
                  </Badge>
                ) : (
                  <span className="text-caption text-fg-muted">
                    {pillarLabel(source.pillars, pillars)}
                    {source.phaseName ? ` · ${source.phaseName}` : ""} · {source.status}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="flex flex-col gap-1 rounded-card bg-page p-4">
        <p className="text-body-medium font-semibold text-fg">Evidence is not an answer yet</p>
        <p className="text-body-small text-fg-muted">
          Uploading or creating an artifact suggests answers. Review the source and confirm the linked answer to close
          a checklist gap.
        </p>
      </div>
    </aside>
  );
}