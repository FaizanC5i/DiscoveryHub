import type { Source } from "../types/source";

export type SourceTypeFilter = "all" | "files" | "notes";

export function isNote(source: Source): boolean {
  return source.source_type === "MANUAL_NOTE";
}

/** Still being extracted, split or mapped, so the row shows a loader. */
export function isWorking(source: Source): boolean {
  return source.processing_status === "processing" || source.mapping_pending;
}

export function filterSourcesByType(sources: Source[], filter: SourceTypeFilter): Source[] {
  if (filter === "all") return sources;
  const wantNotes = filter === "notes";
  return sources.filter((source) => isNote(source) === wantNotes);
}
