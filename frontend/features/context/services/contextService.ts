/**
 * Browser-side document calls. Listing happens on the server, see
 * serverContextService.ts.
 */
import { apiRequest } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import type { Source } from "../types/source";

export function uploadSource(projectId: number, file: File): Promise<Source> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<Source>(API_PATHS.sources.list(projectId), { method: "POST", body });
}

export function reprocessSource(projectId: number, sourceId: number): Promise<Source> {
  return apiRequest<Source>(API_PATHS.sources.reprocess(projectId, sourceId), { method: "POST" });
}

export function deleteSource(projectId: number, sourceId: number): Promise<void> {
  return apiRequest<void>(API_PATHS.sources.detail(projectId, sourceId), { method: "DELETE" });
}