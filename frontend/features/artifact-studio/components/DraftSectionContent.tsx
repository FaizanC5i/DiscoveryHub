"use client";

import { useState } from "react";
import { badgeClass } from "@/features/discovery/utils/class-names";
import type { DraftSection } from "../types/artifact-studio.types";
import { sectionNumber } from "../utils/section-status";

const actionClass =
  "inline-flex cursor-pointer items-center rounded-(--radius-md) border border-(--color-border-default-disabled) " +
  "bg-(--color-bg-default-primary) px-(--space-3) py-(--space-1) text-(length:--font-size-body-small) " +
  "leading-(--line-height-body-small) font-medium text-(--color-text-brand-primary) hover:bg-(--color-bg-brand-subtle) " +
  "disabled:cursor-not-allowed disabled:opacity-70 disabled:hover:bg-(--color-bg-default-primary)";

const saveClass =
  "inline-flex cursor-pointer items-center rounded-(--radius-md) border border-transparent bg-(--color-bg-brand-primary) " +
  "px-(--space-3) py-(--space-1) text-(length:--font-size-body-small) leading-(--line-height-body-small) font-semibold " +
  "text-(--color-text-default-inverse) hover:bg-(--color-bg-brand-secondary) disabled:cursor-not-allowed disabled:opacity-70";

/** What the agent is doing for this section right now. */
export type SectionActivity = "regenerate" | "clarify" | null;

interface DraftSectionContentProps {
  section: DraftSection;
  onSave: (bullets: string[]) => Promise<void>;
  onEditingChange: (isEditing: boolean) => void;
  onRegenerate: () => void;
  onClarify: () => void;
  /** Regenerate or Clarify running for this section. */
  activity: SectionActivity;
  /** True while any agent run is going (the backend runs one at a time per BRD). */
  isAgentBusy: boolean;
  /** Error from the last Regenerate or Clarify for this section. */
  message: string | null;
}

/**
 * One section of the draft: title, Regenerate / Clarify / Edit, and its content.
 * The parent gives this a `key` per section, so edit mode resets when switching sections.
 */
export function DraftSectionContent({
  section,
  onSave,
  onEditingChange,
  onRegenerate,
  onClarify,
  activity,
  isAgentBusy,
  message,
}: DraftSectionContentProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [text, setText] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);

  function startEditing() {
    setText(section.bullets.join("\n"));
    setSaveError(null);
    setIsEditing(true);
    onEditingChange(true);
  }

  function stopEditing() {
    setIsEditing(false);
    onEditingChange(false);
  }

  async function save() {
    setIsSaving(true);
    setSaveError(null);
    try {
      await onSave(lines);
      stopEditing();
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Could not save the section.");
    } finally {
      setIsSaving(false);
    }
  }

  const needsClarification = section.status === "NEEDS_CLARIFICATION";

  return (
    <section
      aria-labelledby={`section-${section.id}-title`}
      className="border-0 border-l-2 border-(--color-border-brand-primary) pl-(--space-5)"
    >
      <div className="mb-(--space-4) flex flex-wrap items-center justify-between gap-(--space-3)">
        <h2
          id={`section-${section.id}-title`}
          className="m-0 text-(length:--font-size-title-medium) leading-(--line-height-title-medium) font-semibold"
        >
          {sectionNumber(section.number)}&nbsp;&nbsp;{section.title}
        </h2>

        {isEditing ? (
          <div className="flex gap-(--space-2)">
            <button type="button" onClick={stopEditing} disabled={isSaving} className={actionClass}>
              Cancel
            </button>
            <button type="button" onClick={() => void save()} disabled={isSaving || lines.length === 0} className={saveClass}>
              {isSaving ? "Saving…" : "Save"}
            </button>
          </div>
        ) : (
          <div className="flex gap-(--space-2)">
            <button
              type="button"
              onClick={onRegenerate}
              disabled={isAgentBusy}
              aria-busy={activity === "regenerate" || undefined}
              title={isAgentBusy && activity !== "regenerate" ? "Wait for the current agent run to finish" : undefined}
              className={actionClass}
            >
              {activity === "regenerate" ? "Regenerating…" : "Regenerate"}
            </button>
            <button
              type="button"
              onClick={onClarify}
              disabled={isAgentBusy}
              aria-busy={activity === "clarify" || undefined}
              title={isAgentBusy && activity !== "clarify" ? "Wait for the current agent run to finish" : undefined}
              className={actionClass}
            >
              {activity === "clarify" ? "Preparing questions…" : "Clarify"}
            </button>
            <button type="button" onClick={startEditing} disabled={activity !== null} className={actionClass}>
              Edit
            </button>
          </div>
        )}
      </div>

      {isEditing ? (
        <div className="flex flex-col gap-(--space-3)">
          <textarea
            id={`edit-${section.id}`}
            aria-label={`Edit ${section.title}, one point per line`}
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={Math.max(4, text.split("\n").length + 1)}
            autoFocus
            className="w-full resize-y rounded-(--radius-md) border-2 border-(--color-border-brand-subtle) bg-(--color-bg-default-primary) px-(--space-5) py-(--space-3) font-(family-name:--font-family-secondary) text-(length:--font-size-body-large) leading-(--line-height-body-large) text-(--color-text-default-secondary) focus-visible:outline-none focus-visible:border-(--color-border-brand-primary)"
          />
          {saveError ? (
            <p role="alert" className="m-0 text-(length:--font-size-body-small) text-(--color-red-700)">
              {saveError}
            </p>
          ) : null}
          <div>
            <span className={badgeClass.warning}>Draft content · Review required</span>
          </div>
        </div>
      ) : needsClarification ? (
        <div className="flex flex-col gap-(--space-3) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium)">
          <p className="m-0 text-(--color-text-default-subtle)">{section.missingReason}</p>
          {section.clarificationQuestions && section.clarificationQuestions.length > 0 && (
            <>
              <p className="m-0 font-semibold">Questions to answer</p>
              <ul className="m-0 list-disc pl-(--space-5)">
                {section.clarificationQuestions.map((q) => (
                  <li key={q} className="mb-(--space-1)">{q}</li>
                ))}
              </ul>
            </>
          )}
          <div>
            <span className={badgeClass.error}>Needs clarification · Not generated</span>
          </div>
        </div>
      ) : (
        <>
          <ul className="m-0 mb-(--space-4) list-disc pl-(--space-5) font-(family-name:--font-family-secondary) text-(length:--font-size-body-large) leading-(--line-height-body-large) text-(--color-text-default-secondary)">
            {section.bullets.map((bullet) => (
              <li key={bullet} className="mb-(--space-1)">{bullet}</li>
            ))}
          </ul>
          <span className={badgeClass.warning}>Draft content · Review required</span>
        </>
      )}

      {message ? (
        <p role="alert" className="m-0 mt-(--space-3) text-(length:--font-size-body-small) leading-(--line-height-body-small) text-(--color-red-700)">
          {message}
        </p>
      ) : null}
    </section>
  );
}