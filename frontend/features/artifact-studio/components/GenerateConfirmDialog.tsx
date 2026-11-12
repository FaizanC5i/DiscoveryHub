"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { CloseIcon } from "@/features/discovery/components/icons";
import { buttonClass } from "@/features/discovery/utils/class-names";
import type { ArtifactReadiness } from "../types/artifact-studio.types";

interface GenerateConfirmDialogProps {
  open: boolean;
  projectId: string;
  artifactName: string;
  readiness: ArtifactReadiness;
  isGenerating: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

/**
 * "Generate before discovery is ready?" popup.
 * Uses the native <dialog>, so Esc closes it and keyboard focus stays inside.
 */
export function GenerateConfirmDialog({
  open,
  projectId,
  artifactName,
  readiness,
  isGenerating,
  onConfirm,
  onClose,
}: GenerateConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    // Always close when this page is hidden or left. Next.js keeps the previous
    // page alive in the background, and an open modal would block the new page.
    return () => {
      if (dialog.open) dialog.close();
    };
  }, [open]);

  const missing = readiness.total - readiness.verified;

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      aria-labelledby="generate-dialog-title"
      className="m-auto w-[min(calc(100%-var(--space-7)),calc(var(--space-64)*3))] rounded-(--radius-xl) border-0 bg-(--color-bg-default-primary) p-(--space-7) text-(--color-text-default-primary) backdrop:bg-(--color-neutral-950)/40 backdrop:backdrop-blur-sm"
    >
      <div className="mb-(--space-4) flex items-start justify-between gap-(--space-4)">
        <h2
          id="generate-dialog-title"
          className="m-0 text-(length:--font-size-title-medium) leading-(--line-height-title-medium) font-medium"
        >
          Generate before discovery is ready?
        </h2>
        <button type="button" onClick={onClose} aria-label="Close" className={buttonClass.icon}>
          <CloseIcon />
        </button>
      </div>

      <div className="flex flex-col gap-(--space-4) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-subtle)">
        <p className="m-0">
          Discovery is {readiness.percent}% complete. This {artifactName} will flag {missing} missing items and exclude{" "}
          {readiness.awaitingReview} unreviewed answers. It will be an incomplete working draft, not client-ready, and
          generating it does not change discovery coverage.
        </p>
        <p className="m-0">Unknowns will be labelled, and only the selected evidence is used.</p>
      </div>

      <div className="mt-(--space-6) flex flex-wrap items-center justify-between gap-(--space-3)">
        <Link
          href={`/projects/${projectId}/discovery`}
          className="text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold text-(--color-text-brand-primary) no-underline hover:underline"
        >
          Resolve gaps first
        </Link>
        <div className="flex gap-(--space-3)">
          <button type="button" onClick={onClose} className={`${buttonClass.subtle} px-(--space-5) py-(--space-3)`}>
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isGenerating}
            className={`${buttonClass.primary} px-(--space-5) py-(--space-3) disabled:cursor-wait disabled:opacity-70`}
          >
            {isGenerating ? "Generating…" : "Approve and generate"}
          </button>
        </div>
      </div>
    </dialog>
  );
}