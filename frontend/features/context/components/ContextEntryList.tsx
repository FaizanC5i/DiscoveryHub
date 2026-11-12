import type { NotesStatus } from "../hooks/useProjectNotes";
import type { ContextEntry } from "../utils/contextEntries";
import { NoteItem } from "./NoteItem";
import { SourceItem } from "./SourceItem";

interface ContextEntryListProps {
  projectId: number;
  entries: ContextEntry[];
  notesStatus: NotesStatus;
  emptyMessage: string;
  onRemoveNote: (noteId: string) => Promise<void>;
}

export function ContextEntryList({
  projectId,
  entries,
  notesStatus,
  emptyMessage,
  onRemoveNote,
}: ContextEntryListProps) {
  return (
    <div className="flex flex-col gap-3">
      {notesStatus === "error" ? (
        <p role="alert" className="text-body-small text-error">
          Notes could not be loaded. Refresh the page to try again.
        </p>
      ) : null}

      {entries.length === 0 ? (
        <p className="text-body-small text-fg-muted">{emptyMessage}</p>
      ) : (
        <ul className="flex flex-col divide-y divide-border-subtle">
          {entries.map((entry) =>
            entry.kind === "source" ? (
              <SourceItem key={entry.id} projectId={projectId} source={entry.source} />
            ) : (
              <NoteItem key={entry.id} note={entry.note} onRemove={onRemoveNote} />
            ),
          )}
        </ul>
      )}
    </div>
  );
}