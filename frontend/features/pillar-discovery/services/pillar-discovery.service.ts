/**
 * Pillar discovery data access. Components never read data directly; they call these functions.
 *
 * BACKEND INTEGRATION: only the bodies of these functions change.
 * Use the shared API client (lib/api/client) like the other services. Keep the return types the same.
 */
import type { PillarId } from "@/features/discovery/types/discovery.types";
import { placeholderUserDiscovery } from "../data/placeholder-data";
import type { PhaseArtifact, PhaseId, PillarDiscovery, RelevantSource } from "../types/pillar-discovery.types";

/**
 * Checklist questions, design-thinking phases with their artifacts, and the
 * context-library sources linked to one pillar.
 * Backend: GET /api/projects/{projectId}/discovery/{pillarId}
 */
export async function getPillarDiscovery(projectId: string, pillarId: PillarId): Promise<PillarDiscovery> {
  // PLACEHOLDER: replace with the API call. Only User Discovery has a design so far.
  void projectId;
  if (pillarId !== "USER") {
    throw new Error("This discovery area is not available yet. Only User Discovery has been designed.");
  }
  return placeholderUserDiscovery;
}

/**
 * Upload a file for one phase artifact. Returns the updated artifact and the new library source.
 * Backend: POST /api/projects/{projectId}/discovery/{pillarId}/phases/{phaseId}/artifacts/{artifactId}
 *          (multipart/form-data, field "file")
 */
export async function uploadPhaseArtifact(
  projectId: string,
  pillarId: PillarId,
  phase: { id: PhaseId; name: string },
  artifact: PhaseArtifact,
  file: File,
  uploadedBy: string,
): Promise<{ artifact: PhaseArtifact; source: RelevantSource }> {
  // PLACEHOLDER: replace with the API call.
  void projectId;
  return {
    artifact: {
      ...artifact,
      status: "uploaded",
      file: { name: file.name, meta: "uploaded just now · processing" },
    },
    source: {
      id: `new-${Date.now()}`,
      title: file.name,
      pillars: [pillarId],
      phaseName: phase.name,
      status: "Processing",
      createdBy: uploadedBy,
    },
  };
}

/**
 * Add files to the context library from this page, linked to the pillar.
 * Backend: POST /api/projects/{projectId}/sources (multipart/form-data, field "files")
 */
export async function uploadPillarSources(
  projectId: string,
  pillarId: PillarId,
  files: File[],
  uploadedBy: string,
): Promise<RelevantSource[]> {
  // PLACEHOLDER: replace with the API call.
  void projectId;
  return files.map((file, i) => ({
    id: `new-${Date.now()}-${i}`,
    title: file.name,
    pillars: [pillarId],
    status: "Processing",
    createdBy: uploadedBy,
  }));
}