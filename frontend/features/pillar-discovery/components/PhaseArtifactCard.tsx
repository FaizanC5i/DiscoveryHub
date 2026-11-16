"use client";

import { useRef } from "react";
import { FileTextIcon } from "@/components/icons";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";
import type { PhaseArtifact, PhaseArtifactStatus } from "../types/pillar-discovery.types";

const STATUS: Record<PhaseArtifactStatus, { label: string; tone: BadgeTone }> = {
  uploaded: { label: "Uploaded", tone: "success" },
  "awaiting-review": { label: "Awaiting review", tone: "warning" },
  draft: { label: "Draft", tone: "brand" },
  "not-started": { label: "Not started", tone: "neutral" },
};

const ACCEPT = ".txt,.md,.docx,.pdf,.xlsx,.pptx,image/*";

/*
 * Compact buttons for artifact cards, as in the design (smaller than Button size "sm"
 * so both actions fit on one line). Colours match the team's Button variants:
 * secondary = brand outline, outline = neutral outline.
 */
const compactButton =
  "inline-flex h-8 shrink-0 items-center justify-center whitespace-nowrap rounded-control px-3 text-body-small font-semibold transition-colors " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong";
const compactSecondary =
  "border border-border-brand bg-surface text-fg-brand hover:border-border-brand-strong hover:text-fg-brand-strong active:bg-surface-brand-subtle";
const compactOutline = "border border-border-disabled bg-surface text-fg hover:bg-surface-muted";

interface PhaseArtifactCardProps {
  artifact: PhaseArtifact;
  position: number; // 1-based
  count: number;
  onUpload: (file: File) => Promise<void>;
}

/** One artifact inside a phase: "ARTIFACT 1 OF 3 · User personas". */
export function PhaseArtifactCard({ artifact, position, count, onUpload }: PhaseArtifactCardProps) {
  const fileInput = useRef<HTMLInputElement>(null);
  const status = STATUS[artifact.status];
  const hasFile = Boolean(artifact.file);

  return (
    <article
      aria-labelledby={`artifact-${artifact.id}`}
      className="flex min-w-0 flex-col gap-3 rounded-card border border-border-disabled bg-page p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-caption font-semibold text-fg-muted">
          ARTIFACT {position} OF {count}
        </p>
        <Badge tone={status.tone} className="rounded-full px-3">
          {status.label}
        </Badge>
      </div>

      <h4 id={`artifact-${artifact.id}`} className="text-title-small font-semibold text-fg">
        {artifact.title}
      </h4>
      <p className="text-body-medium text-fg-muted">{artifact.description}</p>
      <p className="text-body-small text-fg">Informs {artifact.informs.join(", ")}</p>

      {artifact.file ? (
        <div className="flex items-start gap-3 rounded-control border border-border-disabled bg-surface p-3">
          <FileTextIcon className="mt-0.5 size-4 shrink-0 text-fg-brand" />
          <div className="min-w-0">
            <p className="truncate text-body-medium font-semibold text-fg">{artifact.file.name}</p>
            <p className="text-caption text-fg-muted">{artifact.file.meta}</p>
          </div>
        </div>
      ) : null}

      <div className="mt-auto flex flex-col items-start gap-3 pt-2">
        <div className="flex flex-nowrap gap-2">
          {/* PLACEHOLDER: Open and Create in platform have no design yet. */}
          <button type="button" className={cn(compactButton, compactSecondary)}>
            {hasFile ? "Open" : "Create in platform"}
          </button>
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            className={cn(compactButton, compactOutline)}
          >
            {hasFile ? "Replace" : "Upload"}
          </button>
          <input
            ref={fileInput}
            type="file"
            hidden
            accept={ACCEPT}
            aria-label={`Upload a file for ${artifact.title}`}
            onChange={(e) => {
              const file = e.target.files?.[0];
              e.target.value = "";
              if (file) void onUpload(file);
            }}
          />
        </div>
        {/* PLACEHOLDER: templates are not available yet. */}
        <button
          type="button"
          className="text-body-small font-semibold text-fg-brand hover:text-fg-brand-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong"
        >
          Download template
        </button>
      </div>
    </article>
  );
}