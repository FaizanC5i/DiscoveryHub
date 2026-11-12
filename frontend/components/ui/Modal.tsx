"use client";

import { useEffect, useId, useRef, type MouseEvent, type ReactNode } from "react";
import { CloseIcon } from "@/components/icons";
import { cn } from "@/lib/cn";

interface ModalProps {
  open: boolean;
  /** Called on Escape, the close button, or a click on the backdrop. The parent should set open to false. */
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}

/**
 * Dialog built on the browser's native <dialog> element.
 *
 * Analogy: a glass display case set in front of the shop counter. The native
 * dialog does the hard parts for us: it blocks the page behind it (the overlay),
 * keeps the keyboard focus inside, and closes on the Escape key. We only decide
 * when the case is open and what goes inside it.
 *
 * Children are rendered only while open, so a form inside starts fresh every time.
 */
export function Modal({ open, onClose, title, children, className }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  // Escape closes the native dialog and fires "close". Passing that on keeps the parent's state in sync.
  function handleBackdropClick(event: MouseEvent<HTMLDialogElement>) {
    if (event.target === event.currentTarget) onClose();
  }

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
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
              onClick={onClose}
              aria-label="Close"
              className="inline-flex size-9 shrink-0 items-center justify-center rounded-control text-icon hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-border-brand-strong"
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
