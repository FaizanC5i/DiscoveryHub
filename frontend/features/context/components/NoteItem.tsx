"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatProjectTimestamp } from "@/features/project-overview/utils/formatProjectDate";
import type { ProjectNote } from "../types/note";

interface NoteItemProps {
  note: ProjectNote;
  onRemove: (noteId: string) => Promise<void>;
}

export function NoteItem({ note, onRemove }: NoteItemProps) {
  const [isRemoving, setIsRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRemove() {
    setIsRemoving(true);
    setError(null);
    try {
      await onRemove(note.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove this note.");
      setIsRemoving(false);
    }
  }

  return (
    <li className="flex flex-col gap-2 py-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-1">
          <p className="truncate text-body-medium font-semibold text-fg">{note.title}</p>
          <p className="text-caption text-fg-muted">{formatProjectTimestamp(note.created_at)}</p>
        </div>
        <Badge tone="neutral">Note</Badge>
      </div>

      <p className="line-clamp-3 whitespace-pre-line text-body-small text-fg-secondary">{note.body}</p>

      {error ? (
        <p role="alert" className="text-caption text-error">
          {error}
        </p>
      ) : null}

      <div>
        <Button
          size="sm"
          variant="outline"
          loading={isRemoving}
          disabled={isRemoving}
          onClick={handleRemove}
        >
          Remove
        </Button>
      </div>
    </li>
  );
}