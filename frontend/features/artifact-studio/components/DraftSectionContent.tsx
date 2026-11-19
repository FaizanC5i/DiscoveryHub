"use client";

import { useState } from "react";
import { badgeClass } from "@/features/discovery/utils/class-names";
import { MarkdownPreview } from "@/features/mom-assistant/components/MarkdownPreview";
import type { ClarificationAnswer, DraftSection } from "../types/artifact-studio.types";
import { SECTION_STATUS, sectionNumber } from "../utils/section-status";

const actionClass =
  "inline-flex cursor-pointer items-center rounded-(--radius-md) border border-(--color-border-default-disabled) " +
  "bg-(--color-bg-default-primary) px-(--space-3) py-(--space-1) text-(length:--font-size-body-small) " +
  "leading-(--line-height-body-small) font-medium text-(--color-text-brand-primary) hover:bg-(--color-bg-brand-subtle) " +
  "disabled:cursor-not-allowed disabled:opacity-50";

const primaryClass =
  "inline-flex cursor-pointer items-center rounded-(--radius-md) border border-transparent bg-(--color-bg-brand-primary) " +
  "px-(--space-4) py-(--space-2) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold " +
  "text-(--color-text-default-inverse) hover:bg-(--color-bg-brand-secondary) disabled:cursor-not-allowed disabled:opacity-70";

const fieldClass =
  "w-full rounded-(--radius-md) border border-(--color-border-default-primary) bg-(--color-bg-default-primary) p-(--space-3) " +
  "font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) " +
  "focus-visible:outline-none focus-visible:border-(--color-border-brand-strong)";

const noteClass = "m-0 text-(length:--font-size-body-small) leading-(--line-height-body-small)";

interface DraftSectionContentProps {
  section: DraftSection;
  /** True while the agent works on any part of the document: actions wait until it is done. */
  isBusy: boolean;
  onSave: (content: string) => Promise<void>;
  onRegenerate: (answers: ClarificationAnswer[]) => Promise<void>;
  onClarify: () => Promise<void>;
  onEditingChange: (isEditing: boolean) => void;
}

/**
 * One section of the draft: title, Regenerate / Clarify / Edit, its text, and the agent's
 * questions with an answer box each. Answers are sent with Regenerate, so the agent rewrites the
 * section with them; they are saved and reused on every later rewrite.
 */
export function DraftSectionContent({
  section,
  isBusy,
  onSave,
  onRegenerate,
  onClarify,
  onEditingChange,
}: DraftSectionContentProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [text, setText] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSending, setIsSending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const content = section.content ?? section.bullets.map((b) => `- ${b}`).join("\n");
  const questions = section.clarificationQuestions ?? [];
  const actionsDisabled = isBusy || isSending || Boolean(section.isWorking);
  const status = SECTION_STATUS[section.status];

  function startEditing() {
    setText(content);
    setNotice(null);
    setIsEditing(true);
    onEditingChange(true);
  }

  function stopEditing() {
    setIsEditing(false);
    onEditingChange(false);
  }

  async function run(action: () => Promise<void>, onDone?: () => void) {
    setIsSending(true);
    setNotice(null);
    try {
      await action();
      onDone?.();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setIsSending(false);
    }
  }

  function submitAnswers() {
    const filled = questions
      .filter((q) => answers[q]?.trim())
      .map((q) => ({ question: q, answer: answers[q]!.trim() }));
    if (filled.length === 0) {
      setNotice("Type an answer to at least one question first.");
      return;
    }
    void run(() => onRegenerate(filled), () => setAnswers({}));
  }

  return (
    <section
      id={`section-${section.id}`}
      aria-labelledby={`section-${section.id}-title`}
      className="scroll-mt-(--space-8) border-0 border-l-2 border-(--color-border-brand-primary) pl-(--space-5)"
    >
      <div className="mb-(--space-4) flex flex-wrap items-center justify-between gap-(--space-3)">
        <div className="flex flex-wrap items-center gap-(--space-3)">
          <h2
            id={`section-${section.id}-title`}
            className="m-0 text-(length:--font-size-title-medium) leading-(--line-height-title-medium) font-semibold"
          >
            {sectionNumber(section.number)}&nbsp;&nbsp;{section.title}
          </h2>
          <span className={status.badge}>{status.label}</span>
        </div>
        {!isEditing && (
          <div className="flex gap-(--space-2)">
            <button type="button" disabled={actionsDisabled} onClick={() => void run(() => onRegenerate([]))} className={actionClass}>
              Regenerate
            </button>
            <button type="button" disabled={actionsDisabled} onClick={() => void run(onClarify)} className={actionClass}>
              Clarify
            </button>
            <button type="button" disabled={actionsDisabled} onClick={startEditing} className={actionClass}>
              Edit
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-(--space-3)">
        {section.isWorking && (
          <p className={`${noteClass} text-(--color-text-brand-primary)`}>
            The agent is working on this section. It will update by itself when it is done.
          </p>
        )}
        {section.lastError && !section.isWorking && (
          <p role="alert" className={`${noteClass} text-(--color-red-700)`}>{section.lastError}</p>
        )}
        {notice && (
          <p role="alert" className={`${noteClass} text-(--color-red-700)`}>{notice}</p>
        )}

        {isEditing ? (
          <div className="flex flex-col gap-(--space-3)">
            <label htmlFor={`edit-${section.id}`} className={`${noteClass} text-(--color-text-default-subtle)`}>
              Markdown: - bullet points, 1. numbered lists, **bold**, and | tables |
            </label>
            <textarea
              id={`edit-${section.id}`}
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={12}
              className={`${fieldClass} font-mono`}
            />
            <div className="flex gap-(--space-2)">
              <button
                type="button"
                disabled={isSending || !text.trim()}
                onClick={() => void run(() => onSave(text.trim()), stopEditing)}
                className={primaryClass}
              >
                {isSending ? "Saving…" : "Save"}
              </button>
              <button type="button" onClick={stopEditing} className={actionClass}>Cancel</button>
            </div>
          </div>
        ) : content.trim() ? (
          <>
            <MarkdownPreview markdown={content} />
            <div>
              <span className={section.status === "APPROVED" ? badgeClass.success : badgeClass.warning}>
                {section.status === "APPROVED" ? "Approved content" : "Draft content · Review required"}
              </span>
            </div>
          </>
        ) : questions.length === 0 ? (
          <p className={`${noteClass} text-(--color-text-default-subtle)`}>
            No content yet. Click Regenerate to write it, or Clarify to get questions.
          </p>
        ) : null}

        {!isEditing && questions.length > 0 && (
          <div className="flex flex-col gap-(--space-3) rounded-(--radius-md) border border-(--color-border-default-disabled) bg-(--color-bg-default-secondary) p-(--space-4) font-(family-name:--font-family-secondary)">
            {section.missingReason && (
              <p className="m-0 text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-subtle)">
                {section.missingReason}
              </p>
            )}
            <p className="m-0 font-semibold">Questions to answer</p>
            {questions.map((q, i) => (
              <div key={q} className="flex flex-col gap-(--space-1)">
                <label htmlFor={`answer-${section.id}-${i}`} className="text-(length:--font-size-body-medium) leading-(--line-height-body-medium)">
                  {i + 1}. {q}
                </label>
                <textarea
                  id={`answer-${section.id}-${i}`}
                  value={answers[q] ?? ""}
                  onChange={(e) => setAnswers((current) => ({ ...current, [q]: e.target.value }))}
                  placeholder="Your answer…"
                  rows={2}
                  disabled={actionsDisabled}
                  className={fieldClass}
                />
              </div>
            ))}
            <div>
              <button type="button" disabled={actionsDisabled} onClick={submitAnswers} className={primaryClass}>
                {isSending ? "Sending…" : "Submit answers"}
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
