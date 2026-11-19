import type { Source } from "../types/source";
import { isNote } from "../utils/sourceFilters";
import { NoteRow } from "./NoteRow";
import { SourceItem } from "./SourceItem";

interface ContextEntryListProps {
  projectId: number;
  sources: Source[];
  emptyMessage: string;
  onOpenNote: (sourceId: number) => void;
}

/** Files and manual notes in one list. Each kind keeps its own row. */
export function ContextEntryList({ projectId, sources, emptyMessage, onOpenNote }: ContextEntryListProps) {
  if (sources.length === 0) {
    return <p className="text-body-small text-fg-muted">{emptyMessage}</p>;
  }

  return (
    <ul className="flex flex-col divide-y divide-border-subtle">
      {sources.map((source) =>
        isNote(source) ? (
          <NoteRow key={source.id} projectId={projectId} source={source} onOpen={onOpenNote} />
        ) : (
          <SourceItem key={source.id} projectId={projectId} source={source} />
        ),
      )}
    </ul>
  );
}
