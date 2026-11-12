import type { ProjectNote } from "../types/note";
import type { Source } from "../types/source";

export type ContextEntry =
  | { kind: "source"; id: string; createdAt: string; source: Source }
  | { kind: "note"; id: string; createdAt: string; note: ProjectNote };

/** Sources and notes in one list, newest first. */
export function buildContextEntries(sources: Source[], notes: ProjectNote[]): ContextEntry[] {
  const entries: ContextEntry[] = [
    ...sources.map((source) => ({
      kind: "source" as const,
      id: `source-${source.id}`,
      createdAt: source.created_at,
      source,
    })),
    ...notes.map((note) => ({
      kind: "note" as const,
      id: `note-${note.id}`,
      createdAt: note.created_at,
      note,
    })),
  ];
  return entries.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

/** Case-insensitive match on titles, file names and note text. */
export function filterContextEntries(entries: ContextEntry[], query: string): ContextEntry[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return entries;

  return entries.filter((entry) => {
    const fields =
      entry.kind === "source"
        ? [entry.source.title, entry.source.original_filename]
        : [entry.note.title, entry.note.body];
    return fields.some((field) => field.toLowerCase().includes(needle));
  });
}
