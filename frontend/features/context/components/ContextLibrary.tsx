"use client";

import { useMemo, useState } from "react";
import { CloseIcon } from "@/components/icons";
import { YetToBeDone } from "@/components/ui/YetToBeDone";
import { useProjectNotes } from "../hooks/useProjectNotes";
import type { Source } from "../types/source";
import { buildContextEntries, filterContextEntries } from "../utils/contextEntries";
import { AddNoteDialog } from "./AddNoteDialog";
import { ContextActions } from "./ContextActions";
import { ContextEntryList } from "./ContextEntryList";
import { ContextFilters } from "./ContextFilters";

interface ContextLibraryProps {
  projectId: number;
  sources: Source[];
  onHide: () => void;
}

/**
 * The right-hand panel: Add Files, Add Note, filters, and every source and note.
 * Sources come from the server. Notes are loaded and saved through noteService.
 */
export function ContextLibrary({ projectId, sources, onHide }: ContextLibraryProps) {
  const { notes, status, addNote, removeNote } = useProjectNotes(projectId);
  const [isNoteDialogOpen, setIsNoteDialogOpen] = useState(false);
  const [query, setQuery] = useState("");

  const entries = useMemo(() => buildContextEntries(sources, notes), [sources, notes]);
  const visibleEntries = useMemo(() => filterContextEntries(entries, query), [entries, query]);

  const emptyMessage =
    entries.length === 0
      ? "No documents or notes yet. Add files or a note to start."
      : "Nothing matches your search.";

  return (
    <aside
      aria-label="Context library"
      className="flex flex-col gap-5 rounded-card border border-border-subtle bg-surface p-6"
    >
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-title-small font-semibold text-fg">Context library</h2>
        <button
          type="button"
          onClick={onHide}
          aria-label="Hide context library"
          className="inline-flex size-9 shrink-0 items-center justify-center rounded-control text-icon hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-border-brand-strong"
        >
          <CloseIcon className="size-5" />
        </button>
      </div>

      <div className="flex flex-col gap-2 rounded-card bg-page p-4">
        <p className="text-body-small font-semibold text-fg">Discovery progress</p>
        <YetToBeDone />
      </div>

      <ContextActions projectId={projectId} onAddNote={() => setIsNoteDialogOpen(true)} />

      <ContextFilters query={query} onQueryChange={setQuery} />

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-body-medium font-semibold text-fg">Project sources</h3>
          <span className="text-caption text-fg-muted">{entries.length} total</span>
        </div>
        <ContextEntryList
          projectId={projectId}
          entries={visibleEntries}
          notesStatus={status}
          emptyMessage={emptyMessage}
          onRemoveNote={removeNote}
        />
      </section>

      <AddNoteDialog
        open={isNoteDialogOpen}
        onClose={() => setIsNoteDialogOpen(false)}
        onSave={addNote}
      />
    </aside>
  );
}