/**
 * Artifact Studio data access. Components never read data directly; they call these functions.
 *
 * Connected to the backend (backend/app/api/routes/artifact_studio.py). The backend returns the
 * same shapes as artifact-studio.types.ts, so the components did not change.
 * Only the BRD can be generated today; other artifact codes answer ARTIFACT_NOT_AVAILABLE.
 */
import { API_BASE_URL, ApiError, apiRequest } from "@/lib/api/client";
import type {
  ArtifactCode,
  ArtifactDraft,
  ArtifactStudioData,
  ClarificationAnswer,
  DraftConfig,
  DraftSection,
  ExportOptions,
} from "../types/artifact-studio.types";

const projectPath = (projectId: string) => `/api/projects/${encodeURIComponent(projectId)}`;
const artifactPath = (projectId: string, code: ArtifactCode) =>
  `${projectPath(projectId)}/artifacts/${encodeURIComponent(code)}`;

/**
 * Artifact types, generated artifacts, audiences and readiness per artifact type.
 * Backend: GET /api/projects/{projectId}/artifact-studio
 */
export async function getArtifactStudioData(projectId: string): Promise<ArtifactStudioData> {
  return apiRequest<ArtifactStudioData>(`${projectPath(projectId)}/artifact-studio`);
}

/**
 * Start generating a draft from the approved discovery answers. The agent runs in the background
 * (several minutes); the draft editor shows status "Generating" until it is done.
 * Backend: POST /api/projects/{projectId}/artifacts/{code}/generate  body: { title, audience, scope }
 */
export async function generateArtifactDraft(projectId: string, code: ArtifactCode, config: DraftConfig): Promise<void> {
  await apiRequest<{ agentRunId: number }>(`${artifactPath(projectId, code)}/generate`, {
    method: "POST",
    body: JSON.stringify(config),
  });
}

/**
 * The current draft of one artifact, with its sections and versions.
 * Backend: GET /api/projects/{projectId}/artifacts/{code}
 */
export async function getArtifactDraft(projectId: string, code: ArtifactCode): Promise<ArtifactDraft> {
  return apiRequest<ArtifactDraft>(artifactPath(projectId, code));
}

/**
 * Save edited bullet points for one section.
 * Backend: PUT /api/projects/{projectId}/artifacts/{code}/sections/{sectionId}  body: { bullets }
 */
export async function saveDraftSection(
  projectId: string,
  code: ArtifactCode,
  sectionId: string,
  bullets: string[],
): Promise<DraftSection> {
  return apiRequest<DraftSection>(`${artifactPath(projectId, code)}/sections/${encodeURIComponent(sectionId)}`, {
    method: "PUT",
    body: JSON.stringify({ bullets }),
  });
}
/**
 * Rewrite one section with the agent. Pass the Clarify answers to use them; without answers the
 * agent rewrites from the approved discovery answers. Runs in the background: the draft's
 * latestRun is "running" until it is done. Returns the agent run id.
 * Backend: POST /api/projects/{projectId}/artifacts/{code}/sections/{sectionId}/regenerate  body: { answers }
 */
export async function regenerateDraftSection(
  projectId: string,
  code: ArtifactCode,
  sectionId: string,
  answers: ClarificationAnswer[] = [],
): Promise<number> {
  const result = await apiRequest<{ agentRunId: number }>(
    `${artifactPath(projectId, code)}/sections/${encodeURIComponent(sectionId)}/regenerate`,
    { method: "POST", body: JSON.stringify({ answers }) },
  );
  return result.agentRunId;
}

/**
 * Ask the agent for up to 3 questions that would improve one section. Runs in the background;
 * when latestRun finishes, the section's clarificationQuestions hold the questions.
 * Returns the agent run id.
 * Backend: POST /api/projects/{projectId}/artifacts/{code}/sections/{sectionId}/clarify
 */
export async function requestSectionClarification(
  projectId: string,
  code: ArtifactCode,
  sectionId: string,
): Promise<number> {
  const result = await apiRequest<{ agentRunId: number }>(
    `${artifactPath(projectId, code)}/sections/${encodeURIComponent(sectionId)}/clarify`,
    { method: "POST" },
  );
  return result.agentRunId;
}

/**
 * Save the current draft as a new version. Returns the new version number.
 * Backend: POST /api/projects/{projectId}/artifacts/{code}/versions
 */
export async function saveDraftVersion(projectId: string, code: ArtifactCode, currentVersion: number): Promise<number> {
  void currentVersion; // the backend numbers versions itself
  const saved = await apiRequest<{ versionNumber: number; label: string }>(`${artifactPath(projectId, code)}/versions`, {
    method: "POST",
  });
  return saved.versionNumber;
}

/**
 * Export the draft as a file (Markdown, Word or PDF), built by the backend.
 * Backend: GET /api/projects/{projectId}/artifacts/{code}/export?format=md&sources=true&questions=true
 */
export async function exportArtifactDraft(
  projectId: string,
  draft: ArtifactDraft,
  options: ExportOptions,
): Promise<{ fileName: string; blob: Blob }> {
  const query = new URLSearchParams({
    format: options.format,
    sources: String(options.includeSourceReferences),
    questions: String(options.includeOpenQuestions),
  });
  // A file, not JSON, so this uses fetch directly with the session cookies.
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${artifactPath(projectId, draft.artifactCode)}/export?${query}`, {
      credentials: "include",
    });
  } catch {
    throw new ApiError("Cannot reach the server. Please try again.", 0, "NETWORK_ERROR");
  }
  if (!response.ok) {
    let message = "Could not export the draft.";
    let code = "EXPORT_FAILED";
    try {
      const body = await response.json();
      message = body?.detail?.message ?? message;
      code = body?.detail?.code ?? code;
    } catch {
      // keep the generic message
    }
    throw new ApiError(message, response.status, code);
  }
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const fileName =
    /filename="([^"]+)"/.exec(disposition)?.[1] ?? `${draft.artifactCode.toLowerCase()}-draft.${options.format}`;
  return { fileName, blob: await response.blob() };
}
