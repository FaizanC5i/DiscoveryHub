"use client";

import { useEffect, useRef, useState } from "react";
import { InfoIcon } from "@/features/discovery/components/icons";
import { buttonClass } from "@/features/discovery/utils/class-names";
import type { ClarificationAnswer } from "../types/artifact-studio.types";

const fieldClass =
  "w-full rounded-(--radius-md) border border-(--color-border-default-primary) bg-(--color-bg-default-primary) p-(--space-3) " +
  "font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) " +
  "text-(--color-text-default-primary) focus-visible:outline-none focus-visible:border-(--color-border-brand-strong)";

/** Shown in the "What is missing" box when the agent gave no reason. */
const fallbackMissing = (title: string) =>
  `The current ${title} draft is built on statements that no file or context confirms.`;

interface ClarifyDialogProps {
  open: boolean;
  sectionTitle: string;
  /** The agent's questions for this section (up to 3). Empty while they are being prepared. */
  questions: string[];
  /** Why the agent could not write the section, when it said so. */
  missingReason?: string;
  /** The agent is preparing the questions. */
  isPreparing: boolean;
  isSending: boolean;
  error: string | null;
  onGenerate: (answers: ClarificationAnswer[]) => void;
  /** Ask the agent for a fresh set of questions. */
  onNewQuestions: () => void;
  onClose: () => void;
}

/**
 * Clarify popup ("Help us get this section right"): the agent's questions for one section, an
 * answer box for each, and Submit & Regenerate, which sends the answers so the agent rewrites
 * the section with them. Shared by every artifact (BRD, PRD).
 * Uses the native <dialog> like the other Artifact Studio popups (Esc closes it, focus stays inside).
 */
export function ClarifyDialog({
  open,
  sectionTitle,
  questions,
  missingReason,
  isPreparing,
  isSending,
  error,
  onGenerate,
  onNewQuestions,
  onClose,
}: ClarifyDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    // Next.js keeps the previous page alive in the background; an open modal would block the new page.
    return () => {
      if (dialog.open) dialog.close();
    };
  }, [open]);

  function generate() {
    const filled = questions
      .filter((q) => answers[q]?.trim())
      .map((q) => ({ question: q, answer: answers[q]!.trim() }));
    if (filled.length === 0) {
      setNotice("Answer at least one question first.");
      return;
    }
    setNotice(null);
    onGenerate(filled);
  }

  const message = notice ?? error;
  const hasAnswer = questions.some((q) => answers[q]?.trim());

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      aria-labelledby="clarify-dialog-title"
      className="m-auto w-[min(calc(100%-var(--space-7)),calc(var(--space-64)*3))] rounded-(--radius-xl) border-0 bg-(--color-bg-default-primary) p-(--space-7) text-(--color-text-default-primary) backdrop:bg-(--color-neutral-950)/40 backdrop:backdrop-blur-sm"
    >
      <div className="mb-(--space-5) flex flex-col gap-(--space-2)">
        <p className="m-0 text-(length:--font-size-caption) leading-(--line-height-caption) font-semibold tracking-wider uppercase text-(--color-text-default-subtle)">
          Clarify · {sectionTitle}
        </p>
        <h2
          id="clarify-dialog-title"
          className="m-0 text-(length:--font-size-heading-6) leading-(--line-height-heading-6) font-medium"
        >
          Help us get this section right
        </h2>
      </div>

      <div className="flex flex-col gap-(--space-5) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium)">
        <div className="flex gap-(--space-3) rounded-(--radius-lg) border border-(--color-status-warning) bg-(--color-status-warning-light) p-(--space-4) text-(--color-yellow-700)">
          <span className="mt-0.5 inline-flex shrink-0">
            <InfoIcon />
          </span>
          <div className="flex flex-col gap-(--space-1)">
            <p className="m-0 font-semibold">What is missing</p>
            <p className="m-0">{missingReason || fallbackMissing(sectionTitle)}</p>
          </div>
        </div>

        {questions.length === 0 ? (
          <p className="m-0 text-(--color-text-default-subtle)">
            {isPreparing ? "The agent is preparing questions for this section…" : "No questions yet."}
          </p>
        ) : (
          <>
            <p className="m-0 text-(length:--font-size-body-large) leading-(--line-height-body-large) text-(--color-text-default-subtle)">
              Answer what you can; unanswered questions are skipped. The section regenerates from your answers.
            </p>
            {questions.map((q, i) => (
              <div key={q} className="flex flex-col gap-(--space-2)">
                <label
                  htmlFor={`clarify-answer-${i}`}
                  className="text-(length:--font-size-body-large) leading-(--line-height-body-large) font-semibold text-(--color-text-default-primary)"
                >
                  {q}
                </label>
                <textarea
                  id={`clarify-answer-${i}`}
                  value={answers[q] ?? ""}
                  onChange={(e) => setAnswers((current) => ({ ...current, [q]: e.target.value }))}
                  placeholder="Your answer…"
                  rows={4}
                  disabled={isSending}
                  className={fieldClass}
                />
              </div>
            ))}
          </>
        )}

        {message && (
          <p role="alert" className="m-0 text-(length:--font-size-body-small) text-(--color-red-700)">{message}</p>
        )}
      </div>

      <div className="mt-(--space-6) flex flex-wrap items-center justify-between gap-(--space-3)">
        <button
          type="button"
          onClick={onNewQuestions}
          disabled={isPreparing || isSending}
          className="cursor-pointer border-0 bg-transparent p-0 text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold text-(--color-text-brand-primary) hover:underline disabled:cursor-not-allowed disabled:opacity-50"
        >
          Ask for new questions
        </button>
        <div className="flex gap-(--space-3)">
          <button type="button" onClick={onClose} className={`${buttonClass.subtle} px-(--space-5) py-(--space-3)`}>
            Cancel
          </button>
          <button
            type="button"
            onClick={generate}
            disabled={isSending || isPreparing || !hasAnswer}
            className={`${buttonClass.primary} px-(--space-5) py-(--space-3) disabled:cursor-not-allowed disabled:opacity-50`}
          >
            {isSending ? "Regenerating…" : "Submit & Regenerate"}
          </button>
        </div>
      </div>
    </dialog>
  );
}