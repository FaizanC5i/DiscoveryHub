"use client";

import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { ACCEPT_ATTRIBUTE } from "../utils/fileValidation";

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

/** Drag-and-drop area with a Browse button. Only passes files up; validation happens in the hook. */
export function FileDropzone({ onFilesSelected, disabled = false }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  function passFiles(list: FileList | null) {
    if (list && list.length > 0) onFilesSelected(Array.from(list));
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (!disabled) setIsDragging(true);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    if (!disabled) passFiles(event.dataTransfer.files);
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    passFiles(event.target.files);
    event.target.value = ""; // lets the same file be picked again later
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col gap-3 rounded-card border border-dashed p-6 sm:flex-row sm:items-center sm:justify-between",
        isDragging ? "border-border-brand-strong bg-surface-brand-subtle" : "border-border bg-page",
        disabled && "opacity-60",
      )}
    >
      <div className="flex flex-col gap-1">
        <p className="text-body-medium font-semibold text-fg">Drag and drop your files here</p>
        <p className="text-body-small text-fg-muted">PDF, DOCX, TXT, or Markdown · 20 MB each</p>
      </div>

      <Button variant="outline" size="sm" disabled={disabled} onClick={() => inputRef.current?.click()}>
        Browse Files
      </Button>

      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPT_ATTRIBUTE}
        disabled={disabled}
        onChange={handleInputChange}
        className="hidden"
        tabIndex={-1}
        aria-hidden
      />
    </div>
  );
}