"use client";

import { useEffect, useRef, useState } from "react";
import { InfoIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { Textarea } from "@/components/ui/Textarea";
import { cn } from "@/lib/cn";
import type { ClarificationAnswer, DraftSection } from "../types/artifact-studio.types";

interface ClarifyDialogProps {
  /** The section being clarified; null closes the dialog. */
  section: DraftSection | null;
  onClose: () => void;
  /** Called with the answered questions only; unanswered ones are skipped. */
  onSubmit: (answers: ClarificationAnswer[]) => Promise<void>;
}

/*
 * Primary button that stays light purple while disabled, as in the design
 * (the shared Button turns grey when disabled).
 */
const submitClass = cn(
  "inline-flex h-11 items-center justify-center gap-2 rounded-control px-5 text-body-large font-semibold whitespace-nowrap transition-colors",
  "bg-surface-brand text-fg-inverse hover:bg-surface-brand-hover active:bg-surface-brand-pressed",
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong",
  "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-surface-brand",
);

/** Used when the section has questions but no reason from the agent. */
const fallbackMissing = (title: string) =>
  `The current ${title} draft is built on statements that no file or context confirms.`;

/**
 * "Clarify · <section>": the agent's questions for one section, with a text box each.
 * Submit & Regenerate rewrites the section from the answers.
 * Built on the native <dialog>, so Escape closes it and focus stays inside.
 */
export function ClarifyDialog({ section, onClose, onSubmit }: ClarifyDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const open = section !== null;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    // Close when the page is hidden or left: Next.js keeps the previous page alive in the
    // background, and an open modal would block the next page.
    return () => {
      if (dialog.open) dialog.close();
    };
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      aria-labelledby="clarify-dialog-title"
      className="m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] max-w-3xl overflow-y-auto rounded-card border border-border-subtle bg-surface p-0 text-fg backdrop:bg-surface-overlay/60 backdrop:backdrop-blur-sm"
    >
      {/* Keyed by section, so the answers start empty for each section. */}
      {section ? <ClarifyForm key={section.id} section={section} onClose={onClose} onSubmit={onSubmit} /> : null}
    </dialog>
  );
}

function ClarifyForm({
  section,
  onClose,
  onSubmit,
}: {
  section: DraftSection;
  onClose: () => void;
  onSubmit: (answers: ClarificationAnswer[]) => Promise<void>;
}) {
  const questions = section.clarificationQuestions ?? [];
  const [answers, setAnswers] = useState<string[]>(() => questions.map(() => ""));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const answered: ClarificationAnswer[] = questions
    .map((question, i) => ({ question, answer: (answers[i] ?? "").trim() }))
    .filter((item) => item.answer.length > 0);

  async function submit() {
    setIsSubmitting(true);
    setError(null);
    try {
      await onSubmit(answered);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not regenerate the section.");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6 p-6 sm:p-8">
      <div className="flex flex-col gap-2">
        <p className="text-caption font-semibold tracking-wider text-fg-muted uppercase">
          Clarify · {section.title}
        </p>
        <h2 id="clarify-dialog-title" className="text-heading-6 font-medium text-fg">
          Help us get this section right
        </h2>
      </div>

      <div className="flex gap-3 rounded-card border border-warning bg-warning-subtle p-4">
        <InfoIcon className="mt-0.5 size-4 shrink-0 text-badge-warning-fg" />
        <div className="flex flex-col gap-1">
          <p className="text-body-medium font-semibold text-badge-warning-fg">What is missing</p>
          <p className="text-body-medium text-badge-warning-fg">
            {section.missingReason ?? fallbackMissing(section.title)}
          </p>
        </div>
      </div>

      <p className="text-body-large text-fg-muted">
        Answer what you can; unanswered questions are skipped. The section regenerates from your answers.
      </p>

      <div className="flex flex-col gap-5">
        {questions.map((question, i) => (
          <div key={question} className="flex flex-col gap-2">
            <label htmlFor={`clarify-${section.id}-${i}`} className="text-body-large font-semibold text-fg">
              {question}
            </label>
            <Textarea
              id={`clarify-${section.id}-${i}`}
              placeholder="Your answer…"
              value={answers[i] ?? ""}
              onChange={(e) =>
                setAnswers((current) => current.map((value, j) => (j === i ? e.target.value : value)))
              }
              disabled={isSubmitting}
              className="min-h-28"
            />
          </div>
        ))}
      </div>

      {error ? (
        <p role="alert" className="text-body-medium text-badge-error-fg">
          {error}
        </p>
      ) : null}

      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <button
          type="button"
          onClick={() => void submit()}
          disabled={answered.length === 0 || isSubmitting}
          aria-busy={isSubmitting || undefined}
          className={submitClass}
        >
          {isSubmitting ? <Spinner /> : null}
          Submit &amp; Regenerate
        </button>
      </div>
    </div>
  );
}