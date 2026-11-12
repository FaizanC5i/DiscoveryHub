"use client";

import { useEffect, useId, useRef, type MouseEvent, type ReactNode, type SyntheticEvent } from "react";
import { CloseIcon } from "@/components/icons";
import { cn } from "@/lib/cn";

interface ModalProps {
  open: boolean;
  /** Called on Escape, the close button, or a backdrop click, unless dismissible is false. */
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
  /**
   * When false, Escape, the backdrop, and the close button are ignored.
   * Use this while work is running, such as an upload.
   */
  dismissible?: boolean;
}

/**
 * Dialog built on the browser's native <dialog> element.
 *
 * Analogy: a glass display case in front of the counter. The native dialog
 * blocks the page behind it and keeps focus inside. We decide when the case is
 * open and whether a visitor is allowed to close it.
 */
export function Modal({
  open,
  onClose,
  title,
  children,
  className,
  dismissible = true,
}: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  function requestClose() {
    if (dismissible) onClose();
  }

  // Escape fires "cancel" before the browser closes the dialog. Preventing it keeps the dialog open.
  function handleCancel(event: SyntheticEvent<HTMLDialogElement>) {
    if (!dismissible) event.preventDefault();
  }

  function handleBackdropClick(event: MouseEvent<HTMLDialogElement>) {
    if (event.target === event.currentTarget) requestClose();
  }

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      onCancel={handleCancel}
      onClose={onClose}
      onClick={handleBackdropClick}
      className={cn(
        "m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] max-w-3xl overflow-y-auto rounded-card border border-border-subtle bg-surface p-0 text-fg backdrop:bg-surface-overlay/60",
        className,
      )}
    >
      {open ? (
        <div className="flex flex-col gap-8 p-6 sm:p-8">
          <div className="flex items-start justify-between gap-4">
            <h2 id={titleId} className="text-title-medium font-semibold text-fg">
              {title}
            </h2>
            <button
              type="button"
              onClick={requestClose}
              disabled={!dismissible}
              aria-label="Close"
              className="inline-flex size-9 shrink-0 items-center justify-center rounded-control text-icon hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-border-brand-strong disabled:pointer-events-none disabled:opacity-50"
            >
              <CloseIcon className="size-5" />
            </button>
          </div>
          {children}
        </div>
      ) : null}
    </dialog>
  );
}