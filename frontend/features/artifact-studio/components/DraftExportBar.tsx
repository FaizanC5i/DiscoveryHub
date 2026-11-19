"use client";

import { useState } from "react";
import { buttonClass } from "@/features/discovery/utils/class-names";
import type { ExportFormat, ExportOptions } from "../types/artifact-studio.types";

interface DraftExportBarProps {
  isClientReady: boolean;
  onExport: (options: ExportOptions) => Promise<void>;
}

/** Bottom bar: format, export options, and the Export button. */
export function DraftExportBar({ isClientReady, onExport }: DraftExportBarProps) {
  const [format, setFormat] = useState<ExportFormat>("md");
  const [includeSourceReferences, setIncludeSourceReferences] = useState(true);
  const [includeOpenQuestions, setIncludeOpenQuestions] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExport() {
    setIsExporting(true);
    setError(null);
    try {
      await onExport({ format, includeSourceReferences, includeOpenQuestions });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed.");
    } finally {
      setIsExporting(false);
    }
  }

  const checkboxLabel =
    "flex cursor-pointer items-center gap-(--space-2) text-(length:--font-size-body-medium) leading-(--line-height-body-medium)";

  return (
    <div className="sticky bottom-0 z-10 border-t border-(--color-border-default-disabled) bg-(--color-bg-default-primary) px-(--space-4) py-(--space-4) lg:px-(--space-7)">
      <div className="flex flex-wrap items-center justify-between gap-(--space-4)">
        <div className="flex flex-wrap items-center gap-(--space-5)">
          <label className="flex items-center gap-(--space-3) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-subtle)">
            Format
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as ExportFormat)}
              className="rounded-(--radius-md) border border-(--color-border-default-disabled) bg-(--color-bg-default-primary) px-(--space-3) py-(--space-2) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-primary) hover:border-(--color-border-brand-primary)"
            >
              <option value="md">Markdown (.md)</option>
              <option value="docx">Word (.docx)</option>
              <option value="pdf">PDF (.pdf)</option>
            </select>
          </label>
          <label className={checkboxLabel}>
            <input
              type="checkbox"
              checked={includeSourceReferences}
              onChange={(e) => setIncludeSourceReferences(e.target.checked)}
              className="size-(--space-4) accent-(--color-primary-default)"
            />
            Include source references
          </label>
          <label className={checkboxLabel}>
            <input
              type="checkbox"
              checked={includeOpenQuestions}
              onChange={(e) => setIncludeOpenQuestions(e.target.checked)}
              className="size-(--space-4) accent-(--color-primary-default)"
            />
            Include open questions
          </label>
        </div>

        <button
          type="button"
          onClick={() => void handleExport()}
          disabled={isExporting}
          className={`${buttonClass.primary} px-(--space-5) py-(--space-3) disabled:cursor-wait disabled:opacity-70`}
        >
          {isExporting ? "Exporting…" : isClientReady ? "Export draft" : "Export incomplete draft"}
          <span aria-hidden="true">↓</span>
        </button>
      </div>
      {error && (
        <p role="alert" className="m-0 mt-(--space-2) text-right text-(length:--font-size-body-small) leading-(--line-height-body-small) text-(--color-red-700)">
          {error}
        </p>
      )}
    </div>
  );
}