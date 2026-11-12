"use client";

import { useRouter } from "next/navigation";
import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { PlusIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { useSourceUploads } from "../hooks/useSourceUploads";
import { ACCEPT_ATTRIBUTE } from "../utils/fileValidation";
import { PendingFileList } from "./PendingFileList";

interface ContextActionsProps {
  projectId: number;
  onAddNote: () => void;
}

/** Add Files, Add Note, drag-and-drop, and the status of files being uploaded. */
export function ContextActions({ projectId, onAddNote }: ContextActionsProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const { files, fileError, isUploading, addFiles, removeFile, uploadFiles, dropSavedFiles } =
    useSourceUploads();

  async function handleFiles(selected: File[]) {
    const added = addFiles(selected);
    if (added.length === 0) return;
    await uploadFiles(projectId, added);
    dropSavedFiles();
    router.refresh();
  }

  async function handleRetry(id: string) {
    const item = files.find((file) => file.id === id);
    if (!item) return;
    await uploadFiles(projectId, [item]);
    dropSavedFiles();
    router.refresh();
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files) void handleFiles(Array.from(event.target.files));
    event.target.value = ""; // lets the same file be picked again later
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (!isUploading) setIsDragging(true);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    if (!isUploading && event.dataTransfer.files.length > 0) {
      void handleFiles(Array.from(event.dataTransfer.files));
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        onDragOver={handleDragOver}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col gap-3 rounded-card border border-dashed p-4",
          isDragging ? "border-border-brand-strong bg-surface-brand-subtle" : "border-border-subtle",
        )}
      >
        <div className="grid grid-cols-2 gap-3">
          <Button
            size="sm"
            loading={isUploading}
            disabled={isUploading}
            onClick={() => inputRef.current?.click()}
          >
            <PlusIcon className="size-4" />
            Add Files
          </Button>
          <Button size="sm" variant="outline" disabled={isUploading} onClick={onAddNote}>
            <PlusIcon className="size-4" />
            Add Note
          </Button>
        </div>
        <p className="text-caption text-fg-muted">Drop files here, or use Add Files or Add Note.</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPT_ATTRIBUTE}
        onChange={handleInputChange}
        className="hidden"
        tabIndex={-1}
        aria-hidden
      />

      {fileError ? (
        <p role="alert" className="text-caption text-error">
          {fileError}
        </p>
      ) : null}

      <PendingFileList files={files} onRemove={removeFile} onRetry={handleRetry} />
    </div>
  );
}