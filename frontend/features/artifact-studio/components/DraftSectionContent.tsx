"use client";

import { useState } from "react";
import { badgeClass } from "@/features/discovery/utils/class-names";
import { MarkdownPreview } from "@/features/mom-assistant/components/MarkdownPreview";
import type { ClarificationAnswer, DraftSection } from "../types/artifact-studio.types";
import { SECTION_STATUS, sectionNumber } from "../utils/section-status";
import { ClarifyDialog } from "./ClarifyDialog";

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
 * One section of the draft: title, Regenerate / Clarify / Edit, and its text.
 * Regenerate: the agent rewrites the section (saved answers are reused).
 * Clarify: a dialog with the agent's questions (fetched first if there are none), an answer box
 * each, and Generate, which sends the answers to the agent to rewrite the section.
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
  const [isSending, setIsSending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [isClarifyOpen, setIsClarifyOpen] = useState(false);
  const [dialogError, setDialogError] = useState<string | null>(null);
  /** Questions shown when we asked the agent for new ones; cleared when different ones arrive. */
  const [waitingFrom, setWaitingFrom] = useState<string | null>(null);

  const content = section.content ?? section.bullets.map((b) => `- ${b}`).join("\n");
  const questions = section.clarificationQuestions ?? [];
  const actionsDisabled = isBusy || isSending || Boolean(section.isWorking);
  const status = SECTION_STATUS[section.status];
  const questionsKey = questions.join(" | ");
  // Waiting for new questions until different ones arrive, or the run ends with an error.
  const isWaitingForQuestions = waitingFrom !== null && questionsKey === waitingFrom && !section.lastError;
  const isPreparing = isWaitingForQuestions || (Boolean(section.isWorking) && questions.length === 0);

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

  async function askForQuestions() {
    setDialogError(null);
    setWaitingFrom(questionsKey);
    try {
      await onClarify();
    } catch (e) {
      setWaitingFrom(null);
      setDialogError(e instanceof Error ? e.message : "Could not ask the agent for questions.");
    }
  }

  function openClarify() {
    setNotice(null);
    setDialogError(null);
    setIsClarifyOpen(true);
    if (questions.length === 0 && !section.isWorking) void askForQuestions();
  }

  async function generateWithAnswers(answers: ClarificationAnswer[]) {
    setIsSending(true);
    setDialogError(null);
    try {
      await onRegenerate(answers);
      setIsClarifyOpen(false);
    } catch (e) {
      setDialogError(e instanceof Error ? e.message : "Could not send the answers.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section
      id={`section-${section.id}`}
      aria-labelledby={`section-${section.id}-title`}
      className="scroll-mt-(--space-10) border-0 border-l-2 border-(--color-border-brand-primary) pl-(--space-5)"
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
            <button type="button" disabled={isBusy || isSending} onClick={openClarify} className={actionClass}>
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
        ) : (
          <div className="flex flex-col gap-(--space-1)">
            <p className="m-0 text-(length:--font-size-body-large) leading-(--line-height-body-large) text-(--color-text-default-subtle)">
              No context available.
            </p>
            <p className={`${noteClass} text-(--color-text-default-subtle)`}>
              Click Clarify to answer the agent&apos;s questions, or Regenerate to try again.
            </p>
          </div>
        )}
        {!isEditing && content.trim() && questions.length > 0 && (
          <p className={`${noteClass} text-(--color-text-brand-primary)`}>
            The agent has questions for this section. Click Clarify to answer them.
          </p>
        )}
      </div>

      <ClarifyDialog
        open={isClarifyOpen}
        sectionTitle={section.title}
        questions={questions}
        missingReason={section.missingReason}
        isPreparing={isPreparing}
        isSending={isSending}
        error={dialogError ?? (section.lastError && !isPreparing ? section.lastError : null)}
        onGenerate={(answers) => void generateWithAnswers(answers)}
        onNewQuestions={() => void askForQuestions()}
        onClose={() => setIsClarifyOpen(false)}
      />
    </section>
  );
}
