import { API_BASE_URL, apiRequest, toApiError } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import type {
  DocumentKind,
  DownloadFormat,
  GeneratedDocument,
  TranscriptResult,
} from "../types/mom";

export function uploadTranscripts(
  files: File[],
  onProgress: (percent: number) => void,
): Promise<TranscriptResult> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    files.forEach((file) => form.append("files", file));

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}${API_PATHS.mom.transcripts}`);
    xhr.withCredentials = true;

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as TranscriptResult);
        return;
      }
      void toApiError(new Response(xhr.responseText, { status: xhr.status })).then(reject);
    };
    xhr.onerror = () => reject(new Error("Cannot reach the server. Please try again."));
    xhr.ontimeout = () => reject(new Error("The upload timed out. Please try again."));
    xhr.send(form);
  });
}

export function generateMinutes(transcript: string): Promise<GeneratedDocument> {
  return apiRequest<GeneratedDocument>(API_PATHS.mom.minutes, {
    method: "POST",
    body: JSON.stringify({ transcript }),
  });
}

export function generateDetailedSummary(transcript: string, previousMom: unknown): Promise<GeneratedDocument> {
  return apiRequest<GeneratedDocument>(API_PATHS.mom.detailedSummary, {
    method: "POST",
    body: JSON.stringify({ transcript, previous_mom: previousMom }),
  });
}

export async function downloadDocument(
  kind: DocumentKind,
  format: DownloadFormat,
  output: unknown,
  projectName: string | null,
  sourceName: string | null,
): Promise<{ blob: Blob; filename: string }> {
  const response = await fetch(`${API_BASE_URL}${API_PATHS.mom.download}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document: kind, format, output, project_name: projectName, source_name: sourceName }),
  }).catch(() => {
    throw new Error("Cannot reach the server. Please try again.");
  });

  if (!response.ok) throw await toApiError(response);

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="([^"]+)"/.exec(disposition);
  return { blob: await response.blob(), filename: match?.[1] ?? `meeting.${format}` };
}

export interface AttachResult {
  project_id: number;
  ok: boolean;
  error?: string;
}

export function attachToProjects(
  kind: DocumentKind,
  output: unknown,
  projectIds: number[],
  projectName: string | null,
  sourceName: string | null,
): Promise<{ results: AttachResult[] }> {
  return apiRequest<{ results: AttachResult[] }>(API_PATHS.mom.attach, {
    method: "POST",
    body: JSON.stringify({
      project_ids: projectIds,
      document: kind,
      output,
      project_name: projectName,
      source_name: sourceName,
    }),
  });
}

export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
