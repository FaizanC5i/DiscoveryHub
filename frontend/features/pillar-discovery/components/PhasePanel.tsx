import { ChevronDownIcon, ChevronUpIcon, PlusIcon } from "@/components/icons";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";
import type { DesignPhase } from "../types/pillar-discovery.types";
import { helpsAnswerLabel, phaseNumber } from "../utils/pillar-progress";
import { PhaseArtifactCard } from "./PhaseArtifactCard";

interface PhasePanelProps {
  phase: DesignPhase;
  openQuestionCount: number;
  isExpanded: boolean;
  onToggle: () => void;
  onUploadArtifact: (artifactId: string, file: File) => Promise<void>;
}

/** One phase in the accordion. Expanded, it shows the phase's artifacts. */
export function PhasePanel({ phase, openQuestionCount, isExpanded, onToggle, onUploadArtifact }: PhasePanelProps) {
  const bodyId = `phase-${phase.id}-body`;

  return (
    <section
      id={`phase-${phase.id}`}
      aria-labelledby={`phase-${phase.id}-title`}
      className={cn(
        "scroll-mt-6 rounded-card border bg-surface",
        isExpanded ? "border-border-brand" : "border-border-disabled",
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={bodyId}
        className="flex w-full items-start gap-4 rounded-card p-6 text-left focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-border-brand-strong"
      >
        <span
          aria-hidden="true"
          className={cn(
            "inline-flex size-10 shrink-0 items-center justify-center rounded-control text-body-large font-bold",
            isExpanded ? "bg-surface-brand text-fg-inverse" : "bg-surface-muted text-fg",
          )}
        >
          {phaseNumber(phase.number)}
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-1">
          <span id={`phase-${phase.id}-title`} className="text-title-large font-medium text-fg">
            {phase.name}
          </span>
          <span className="text-body-large text-fg-muted">{phase.tagline}</span>
        </span>
        {isExpanded ? (
          <ChevronUpIcon className="mt-2 size-5 shrink-0 text-icon" />
        ) : (
          <ChevronDownIcon className="mt-2 size-5 shrink-0 text-icon" />
        )}
      </button>

      {isExpanded ? (
        <div id={bodyId} className="flex flex-col gap-5 px-6 pb-6 sm:pl-20">
          <p className="text-body-large text-fg">{phase.description}</p>

          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="brand" className="rounded-full px-3 py-1 text-body-small">
              {helpsAnswerLabel(openQuestionCount)}
            </Badge>
            {phase.questionIds.map((id) => (
              <span
                key={id}
                className="inline-flex items-center rounded-full border border-border-brand px-3 py-0.5 text-body-small font-medium text-fg-brand"
              >
                {id}
              </span>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {phase.artifacts.map((artifact, index) => (
              <PhaseArtifactCard
                key={artifact.id}
                artifact={artifact}
                position={index + 1}
                count={phase.artifacts.length}
                onUpload={(file) => onUploadArtifact(artifact.id, file)}
              />
            ))}
          </div>

          {/* PLACEHOLDER: adding a custom artifact has no design yet. */}
          <button
            type="button"
            className="flex flex-col items-center gap-1 rounded-card border border-dashed border-border px-4 py-8 text-center hover:bg-page focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong"
          >
            <PlusIcon className="size-5 text-fg-brand" />
            <span className="text-body-large font-semibold text-fg-brand">Add artifact</span>
            <span className="text-body-small text-fg-muted">Create or upload another {phase.name} artifact</span>
          </button>
        </div>
      ) : null}
    </section>
  );
}