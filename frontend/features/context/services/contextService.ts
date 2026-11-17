/**
 * Browser-side document and note calls. The first listing happens on the server, see
 * serverContextService.ts. Search goes back to the server so note text is matched there.
 */
import { apiRequest } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import type { NoteDetail, NoteInput } from "../types/note";
import type { Source } from "../types/source";

export function uploadSource(projectId: number, file: File): Promise<Source> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<Source>(API_PATHS.sources.list(projectId), { method: "POST", body });
}

export function listSources(projectId: number, query: string): Promise<Source[]> {
  const params = new URLSearchParams({ q: query });
  return apiRequest<Source[]>(`${API_PATHS.sources.list(projectId)}?${params.toString()}`);
}

export function reprocessSource(projectId: number, sourceId: number): Promise<Source> {
  return apiRequest<Source>(API_PATHS.sources.reprocess(projectId, sourceId), { method: "POST" });
}

export function deleteSource(projectId: number, sourceId: number): Promise<void> {
  return apiRequest<void>(API_PATHS.sources.detail(projectId, sourceId), { method: "DELETE" });
}

export function createNote(projectId: number, input: NoteInput): Promise<Source> {
  return apiRequest<Source>(API_PATHS.notes.list(projectId), {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getNote(projectId: number, noteId: number): Promise<NoteDetail> {
  return apiRequest<NoteDetail>(API_PATHS.notes.detail(projectId, noteId));
}

export function updateNote(projectId: number, noteId: number, input: NoteInput): Promise<Source> {
  return apiRequest<Source>(API_PATHS.notes.detail(projectId, noteId), {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}
