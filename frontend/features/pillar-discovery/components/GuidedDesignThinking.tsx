import { cn } from "@/lib/cn";
import type { ChecklistQuestion, DesignPhase, PhaseId } from "../types/pillar-discovery.types";
import { countOpenQuestions, helpsAnswerLabel, phaseNumber } from "../utils/pillar-progress";
import { PhasePanel } from "./PhasePanel";

interface GuidedDesignThinkingProps {
  phases: DesignPhase[];
  questions: ChecklistQuestion[];
  activePhaseId: PhaseId | null;
  onSelectPhase: (phaseId: PhaseId) => void;
  onTogglePhase: (phaseId: PhaseId) => void;
  onUploadArtifact: (phaseId: PhaseId, artifactId: string, file: File) => Promise<void>;
}

/** "Guided design thinking": the five phase tiles, then one accordion panel per phase. */
export function GuidedDesignThinking({
  phases,
  questions,
  activePhaseId,
  onSelectPhase,
  onTogglePhase,
  onUploadArtifact,
}: GuidedDesignThinkingProps) {
  return (
    <section aria-labelledby="guided-design-thinking-title" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 id="guided-design-thinking-title" className="text-heading-6 font-semibold text-fg">
          Guided design thinking
        </h2>
        <p className="max-w-4xl text-body-large text-fg-muted">
          Work through a phase to gather evidence. Each phase can hold several artifacts, created in the platform or
          uploaded. Start anywhere and return as you learn.
        </p>
      </div>

      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {phases.map((phase) => {
          const isActive = phase.id === activePhaseId;
          return (
            <li key={phase.id} className="min-w-0">
              <button
                type="button"
                onClick={() => onSelectPhase(phase.id)}
                aria-pressed={isActive}
                className={cn(
                  "flex h-full w-full min-w-0 flex-col items-start gap-2 rounded-card border p-4 text-left transition-colors",
                  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong",
                  isActive
                    ? "border-border-brand bg-surface-brand-subtle"
                    : "border-border-disabled bg-surface hover:border-border-brand-subtle",
                )}
              >
                <span className="text-caption text-fg-muted">{phaseNumber(phase.number)}</span>
                <span className="text-title-small font-medium text-fg">{phase.name}</span>
                {/* Same colours as the brand Badge, but allowed to wrap so it never leaves the tile. */}
                <span className="max-w-full rounded-full bg-badge-brand-bg px-2.5 py-0.5 text-caption font-medium text-badge-brand-fg">
                  {helpsAnswerLabel(countOpenQuestions(phase, questions))}
                </span>
              </button>
            </li>
          );
        })}
      </ul>

      <div className="flex flex-col gap-4">
        {phases.map((phase) => (
          <PhasePanel
            key={phase.id}
            phase={phase}
            openQuestionCount={countOpenQuestions(phase, questions)}
            isExpanded={phase.id === activePhaseId}
            onToggle={() => onTogglePhase(phase.id)}
            onUploadArtifact={(artifactId, file) => onUploadArtifact(phase.id, artifactId, file)}
          />
        ))}
      </div>
    </section>
  );
}