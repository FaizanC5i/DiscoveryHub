import type { SourceStatus } from "./source";

/** The title and text the note form sends. */
export type NoteInput = {
  title: string;
  body: string;
};

/** A manual note with its full text, from GET /api/projects/{id}/notes/{noteId}. */
export interface NoteDetail {
  id: number;
  project_id: number;
  title: string;
  body: string;
  processing_status: SourceStatus;
  failure_reason: string | null;
  chunk_count: number;
  created_by_name: string;
  created_at: string;
  updated_at: string | null;
}

export type NoteFormValues = NoteInput;
