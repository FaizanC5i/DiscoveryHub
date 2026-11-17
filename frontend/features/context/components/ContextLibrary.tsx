"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { CloseIcon } from "@/components/icons";
import { YetToBeDone } from "@/components/ui/YetToBeDone";
import { useLiveSources } from "../hooks/useLiveSources";
import { useSourceSearch } from "../hooks/useSourceSearch";
import { createNote } from "../services/contextService";
import type { NoteInput } from "../types/note";
import type { Source } from "../types/source";
import { filterSourcesByType, isWorking, type SourceTypeFilter } from "../utils/sourceFilters";
import { AddNoteDialog } from "./AddNoteDialog";
import { ContextActions } from "./ContextActions";
import { ContextEntryList } from "./ContextEntryList";
import { ContextFilters } from "./ContextFilters";
import { NoteDetailDialog } from "./NoteDetailDialog";
import { ProcessingPanel } from "./ProcessingIndicator";

interface ContextLibraryProps {
  projectId: number;
  sources: Source[];
  onHide: () => void;
}

/**
 * The right-hand panel: Add Files, Add Note, filters, and every file and note.
 * Sources come from the server. Notes are created, opened, and edited through the same API.
 */
export function ContextLibrary({ projectId, sources: serverSources, onHide }: ContextLibraryProps) {
  const { sources, addSaved } = useLiveSources(projectId, serverSources);
  const router = useRouter();
  const [isNoteDialogOpen, setIsNoteDialogOpen] = useState(false);
  const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<SourceTypeFilter>("all");

  const workingCount = useMemo(() => sources.filter(isWorking).length, [sources]);

  const { visible: searched, error: searchError } = useSourceSearch(projectId, query, sources);
  const visibleSources = useMemo(() => filterSourcesByType(searched, typeFilter), [searched, typeFilter]);

  const emptyMessage =
    sources.length === 0
      ? "No documents or notes yet. Add files or a note to start."
      : "Nothing matches your search or filter.";

  async function handleSaveNote(input: NoteInput) {
    addSaved([await createNote(projectId, input)]);
    router.refresh();
  }

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

      <ContextActions projectId={projectId} onAddNote={() => setIsNoteDialogOpen(true)} onSaved={addSaved} />

      <ContextFilters
        query={query}
        onQueryChange={setQuery}
        typeFilter={typeFilter}
        onTypeFilterChange={setTypeFilter}
      />

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-body-medium font-semibold text-fg">Project sources</h3>
          <span className="text-caption text-fg-muted">{sources.length} total</span>
        </div>
        {workingCount > 0 ? <ProcessingPanel count={workingCount} /> : null}
        {searchError ? (
          <p role="alert" className="text-caption text-error">
            {searchError}
          </p>
        ) : null}
        <ContextEntryList
          projectId={projectId}
          sources={visibleSources}
          emptyMessage={emptyMessage}
          onOpenNote={setSelectedNoteId}
        />
      </section>

      <AddNoteDialog
        open={isNoteDialogOpen}
        onClose={() => setIsNoteDialogOpen(false)}
        onSave={handleSaveNote}
      />

      {selectedNoteId !== null ? (
        <NoteDetailDialog
          key={selectedNoteId}
          projectId={projectId}
          sourceId={selectedNoteId}
          onClose={() => setSelectedNoteId(null)}
        />
      ) : null}
    </aside>
  );
}
