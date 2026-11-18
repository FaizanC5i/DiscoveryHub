import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { ChecklistQuestion } from "../types/pillar-discovery.types";

interface QuestionCardProps {
  question: ChecklistQuestion;
  phaseName: string;
  onGetHelp: () => void;
}

/** One checklist item in the horizontal list: Q01 · OPEN · Empathize. */
export function QuestionCard({ question, phaseName, onGetHelp }: QuestionCardProps) {
  const isOpen = question.status === "open";

  return (
    <article
      aria-labelledby={`question-${question.id}`}
      className="flex w-90 shrink-0 snap-start flex-col gap-3 rounded-card border border-border-disabled bg-surface p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-caption font-semibold text-fg-muted">
          {question.id} · {isOpen ? "OPEN" : "ANSWERED"} · {phaseName}
        </p>
        {isOpen ? (
          question.priority === "critical" ? (
            <Badge tone="error" className="rounded-full px-3">Critical gap</Badge>
          ) : (
            <Badge tone="warning" className="rounded-full px-3">Recommended</Badge>
          )
        ) : (
          <Badge tone="success" className="rounded-full px-3">Answered</Badge>
        )}
      </div>

      <h3 id={`question-${question.id}`} className="text-title-small font-semibold text-fg">
        {question.question}
      </h3>

      <p className="text-body-medium text-fg-muted">
        <span className="font-semibold text-fg">{isOpen ? "Missing:" : "Answer:"}</span>{" "}
        {isOpen ? question.missing : question.answer}
      </p>

      <div className="flex flex-wrap items-center gap-2 text-caption text-fg-muted">
        <span>Source:</span>
        {question.sources.map((source) => (
          <Badge key={source} tone="neutral" className="rounded-full px-2.5">
            {source}
          </Badge>
        ))}
      </div>

      <div className="mt-auto flex flex-wrap items-center gap-4 border-t border-border-disabled pt-4">
        {/* PLACEHOLDER: the answer form has no design yet. */}
        <Button variant="secondary" size="sm">
          {isOpen ? "Answer" : "View answer"}
        </Button>
        <button
          type="button"
          onClick={onGetHelp}
          className="text-body-medium font-semibold text-fg-brand hover:text-fg-brand-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong"
        >
          Get help: {phaseName} <span aria-hidden="true">↓</span>
        </button>
      </div>
    </article>
  );
}