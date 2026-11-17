/** A document as returned by GET /api/projects/{id}/sources. Manual notes are included. */
export type SourceStatus = "processing" | "ready" | "failed";

export type SourceType = "FILE_UPLOAD" | "MANUAL_NOTE";

export interface Source {
  id: number;
  project_id: number;
  source_type: SourceType;
  title: string;
  original_filename: string | null;
  mime_type: string;
  file_size_bytes: number;
  processing_status: SourceStatus;
  failure_reason: string | null;
  created_at: string;
  updated_at: string | null;
  /** True while the helper agent still has chunks of this source to map. */
  mapping_pending: boolean;
}

/** The state of a file the user has picked, before or during upload. */
export type UploadState = "queued" | "uploading" | "done" | "failed";

export interface PendingFile {
  id: string;
  file: File;
  state: UploadState;
  error?: string;
  /** Set once the server has created the source, so Retry reprocesses instead of re-uploading. */
  sourceId?: number;
}
