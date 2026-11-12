/**
 * Artifact Studio data access. Components never read data directly; they call these functions.
 *
 * BACKEND INTEGRATION: only the bodies of these functions change.
 * Use the same API helper your dashboard services use. Keep the return types the same.
 */
import { artifactTypes, audiences, availableArtifacts, placeholderDraft, placeholderReadiness } from "../data/placeholder-data";
import type {
  ArtifactCode,
  ArtifactDraft,
  ArtifactReadiness,
  ArtifactStudioData,
  DraftConfig,
  DraftSection,
  ExportOptions,
} from "../types/artifact-studio.types";

/**
 * Artifact types, generated artifacts, audiences and readiness per artifact type.
 * Backend: GET /api/projects/{projectId}/artifact-studio
 */
export async function getArtifactStudioData(projectId: string): Promise<ArtifactStudioData> {
  // PLACEHOLDER: replace with the API call. projectId is used by the real request.
  void projectId;
  const readiness = Object.fromEntries(
    artifactTypes.map((t) => [t.code, placeholderReadiness]),
  ) as Record<ArtifactCode, ArtifactReadiness>;

  return { artifactTypes, availableArtifacts, audiences, readiness };
}

/**
 * Start generating a draft from the approved discovery answers.
 * Backend: POST /api/projects/{projectId}/artifacts/{code}/generate  body: { title, audience, scope }
 */
export async function generateArtifactDraft(projectId: string, code: ArtifactCode, config: DraftConfig): Promise<void> {
  // PLACEHOLDER: replace with the API call.
  void projectId;
  void code;
  void config;
}

/**
 * The current draft of one artifact, with its sections and versions.
 * Backend: GET /api/projects/{projectId}/artifacts/{code}
 */
export async function getArtifactDraft(projectId: string, code: ArtifactCode): Promise<ArtifactDraft> {
  // PLACEHOLDER: replace with the API call.
  void projectId;
  const type = artifactTypes.find((t) => t.code === code);
  if (!type) throw new Error("This artifact type does not exist.");
  return {
    ...placeholderDraft,
    artifactCode: code,
    artifactName: type.description,
  };
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
  // PLACEHOLDER: replace with the API call.
  void projectId;
  void code;
  const section = placeholderDraft.sections.find((s) => s.id === sectionId)!;
  return { ...section, bullets, status: "PENDING_REVIEW" };
}

/**
 * Save the current draft as a new version. Returns the new version number.
 * Backend: POST /api/projects/{projectId}/artifacts/{code}/versions
 */
export async function saveDraftVersion(projectId: string, code: ArtifactCode, currentVersion: number): Promise<number> {
  // PLACEHOLDER: replace with the API call.
  void projectId;
  void code;
  return currentVersion + 1;
}

/**
 * Export the draft as a file.
 * Backend: GET /api/projects/{projectId}/artifacts/{code}/export?format=md&sources=true&questions=true
 */
export async function exportArtifactDraft(
  projectId: string,
  draft: ArtifactDraft,
  options: ExportOptions,
): Promise<{ fileName: string; blob: Blob }> {
  // PLACEHOLDER: builds Markdown in the browser. The backend will create Word and PDF files.
  void projectId;
  if (options.format !== "md") {
    throw new Error("Word and PDF export will work once the backend is connected. Choose Markdown for now.");
  }

  const lines: string[] = [`# ${draft.title}: ${draft.artifactName}`, "", draft.description, ""];
  if (!draft.isClientReady) {
    lines.push("> Incomplete draft: discovery is not complete. Not client-ready.", "");
  }
  for (const section of draft.sections) {
    lines.push(`## ${String(section.number).padStart(2, "0")} ${section.title}`, "");
    section.bullets.forEach((b) => lines.push(`- ${b}`));
    if (options.includeOpenQuestions && section.clarificationQuestions?.length) {
      lines.push("", "**Open questions**", "");
      section.clarificationQuestions.forEach((q) => lines.push(`- ${q}`));
    }
    lines.push("");
  }
  if (options.includeSourceReferences) {
    lines.push("---", "", `Sources: ${draft.snapshot.sources} project source(s).`);
  }

  return {
    fileName: `${draft.artifactCode.toLowerCase()}-draft.md`,
    blob: new Blob([lines.join("\n")], { type: "text/markdown" }),
  };
}