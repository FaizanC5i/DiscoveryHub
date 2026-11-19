"use client";

import { useEffect, useRef, useState } from "react";
import { CloseIcon } from "@/features/discovery/components/icons";
import { buttonClass } from "@/features/discovery/utils/class-names";
import type { ClarificationAnswer } from "../types/artifact-studio.types";

const fieldClass =
  "w-full rounded-(--radius-md) border border-(--color-border-default-primary) bg-(--color-bg-default-primary) p-(--space-3) " +
  "font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) " +
  "text-(--color-text-default-primary) focus-visible:outline-none focus-visible:border-(--color-border-brand-strong)";

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
 * Clarify popup: the agent's questions for one section, an answer box for each, and Generate.
 * Generate sends the answers to the agent, which rewrites the section with them.
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

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      aria-labelledby="clarify-dialog-title"
      className="m-auto w-[min(calc(100%-var(--space-7)),calc(var(--space-64)*3))] rounded-(--radius-xl) border-0 bg-(--color-bg-default-primary) p-(--space-7) text-(--color-text-default-primary) backdrop:bg-(--color-neutral-950)/40 backdrop:backdrop-blur-sm"
    >
      <div className="mb-(--space-4) flex items-start justify-between gap-(--space-4)">
        <h2
          id="clarify-dialog-title"
          className="m-0 text-(length:--font-size-title-medium) leading-(--line-height-title-medium) font-medium"
        >
          Clarify: {sectionTitle}
        </h2>
        <button type="button" onClick={onClose} aria-label="Close" className={buttonClass.icon}>
          <CloseIcon />
        </button>
      </div>

      <div className="flex flex-col gap-(--space-4) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium)">
        {missingReason && <p className="m-0 text-(--color-text-default-subtle)">{missingReason}</p>}

        {questions.length === 0 ? (
          <p className="m-0 text-(--color-text-default-subtle)">
            {isPreparing ? "The agent is preparing questions for this section…" : "No questions yet."}
          </p>
        ) : (
          <>
            <p className="m-0 text-(--color-text-default-subtle)">
              Answer the agent&apos;s questions, then click Generate. Only the facts you give are added.
            </p>
            {questions.map((q, i) => (
              <div key={q} className="flex flex-col gap-(--space-2)">
                <label htmlFor={`clarify-answer-${i}`} className="font-semibold text-(--color-text-default-primary)">
                  {i + 1}. {q}
                </label>
                <textarea
                  id={`clarify-answer-${i}`}
                  value={answers[q] ?? ""}
                  onChange={(e) => setAnswers((current) => ({ ...current, [q]: e.target.value }))}
                  placeholder="Your answer…"
                  rows={3}
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
            disabled={isSending || isPreparing || questions.length === 0}
            className={`${buttonClass.primary} px-(--space-5) py-(--space-3) disabled:cursor-wait disabled:opacity-70`}
          >
            {isSending ? "Generating…" : "Generate"}
          </button>
        </div>
      </div>
    </dialog>
  );
}
