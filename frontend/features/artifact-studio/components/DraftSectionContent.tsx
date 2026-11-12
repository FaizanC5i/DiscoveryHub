"use client";

import { useState } from "react";
import { badgeClass } from "@/features/discovery/utils/class-names";
import type { DraftSection } from "../types/artifact-studio.types";
import { sectionNumber } from "../utils/section-status";

const actionClass =
  "inline-flex cursor-pointer items-center rounded-(--radius-md) border border-(--color-border-default-disabled) " +
  "bg-(--color-bg-default-primary) px-(--space-3) py-(--space-1) text-(length:--font-size-body-small) " +
  "leading-(--line-height-body-small) font-medium text-(--color-text-brand-primary) hover:bg-(--color-bg-brand-subtle)";

interface DraftSectionContentProps {
  section: DraftSection;
  onSave: (bullets: string[]) => Promise<void>;
  onEditingChange: (isEditing: boolean) => void;
}

/**
 * One section of the draft: title, Regenerate / Clarify / Edit, and its content.
 * The parent gives this a `key` per section, so edit mode resets when switching sections.
 */
export function DraftSectionContent({ section, onSave, onEditingChange }: DraftSectionContentProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [text, setText] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  function startEditing() {
    setText(section.bullets.join("\n"));
    setIsEditing(true);
    onEditingChange(true);
  }

  function stopEditing() {
    setIsEditing(false);
    onEditingChange(false);
  }

  async function save() {
    setIsSaving(true);
    await onSave(text.split("\n").map((line) => line.trim()).filter(Boolean));
    setIsSaving(false);
    stopEditing();
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
        {!isEditing && (
          <div className="flex gap-(--space-2)">
            {/* PLACEHOLDER: Regenerate and Clarify need the BRD agent API. */}
            <button type="button" className={actionClass}>Regenerate</button>
            <button type="button" className={actionClass}>Clarify</button>
            <button type="button" onClick={startEditing} className={actionClass}>Edit</button>
          </div>
        )}
      </div>

      {isEditing ? (
        <div className="flex flex-col gap-(--space-3)">
          <label
            htmlFor={`edit-${section.id}`}
            className="text-(length:--font-size-body-small) leading-(--line-height-body-small) text-(--color-text-default-subtle)"
          >
            One point per line
          </label>
          <textarea
            id={`edit-${section.id}`}
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={6}
            className="w-full rounded-(--radius-md) border border-(--color-border-default-primary) bg-(--color-bg-default-primary) p-(--space-3) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) focus-visible:outline-none focus-visible:border-(--color-border-brand-strong)"
          />
          <div className="flex gap-(--space-2)">
            <button
              type="button"
              onClick={() => void save()}
              disabled={isSaving}
              className="inline-flex cursor-pointer items-center rounded-(--radius-md) border border-transparent bg-(--color-bg-brand-primary) px-(--space-4) py-(--space-2) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold text-(--color-text-default-inverse) hover:bg-(--color-bg-brand-secondary) disabled:opacity-70"
            >
              {isSaving ? "Saving…" : "Save"}
            </button>
            <button type="button" onClick={stopEditing} className={actionClass}>Cancel</button>
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
    </section>
  );
}