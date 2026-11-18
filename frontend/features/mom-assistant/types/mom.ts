export type DocumentKind = "mom" | "detailed-summary";
export type DownloadFormat = "docx" | "md" | "json";

export interface TranscriptFileInfo {
  name: string;
  type: string;
  size: number;
  characters: number;
}

export interface TranscriptResult {
  transcript: string;
  files: TranscriptFileInfo[];
}

export interface GeneratedDocument {
  output: unknown;
  project_name: string;
  preview: string;
}

export const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

export const TRANSCRIPT_FORMATS = "TXT, MD, VTT, SRT, DOCX, PDF, HTML, RTF, JSON, CSV, LOG";
