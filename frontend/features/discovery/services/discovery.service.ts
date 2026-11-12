/**
 * Discovery data access. Components never read data directly; they call these functions.
 *
 * BACKEND INTEGRATION: only the bodies of these functions change.
 * Use the same API helper your dashboard services use (it sends the login cookies).
 * Keep the return types the same and nothing else in the app needs to change.
 */
import {
  placeholderPillars,
  placeholderProject,
  placeholderSources,
  placeholderUser,
  TARGET_PERCENT,
} from "../data/placeholder-data";
import type { DiscoveryOverview, Source } from "../types/discovery.types";

/**
 * Project, user, pillars with gaps, and context sources.
 * Backend: GET /api/projects/{projectId}/discovery
 */
export async function getDiscoveryOverview(projectId: string): Promise<DiscoveryOverview> {
  // PLACEHOLDER: replace with the API call.
  return {
    project: { id: projectId, name: placeholderProject.name },
    user: placeholderUser,
    targetPercent: TARGET_PERCENT,
    pillars: placeholderPillars,
    sources: placeholderSources,
  };
}

/**
 * Upload files to the context library. Returns the new sources.
 * Backend: POST /api/projects/{projectId}/sources (multipart/form-data, field "files")
 */
export async function uploadSourceFiles(projectId: string, files: File[]): Promise<Source[]> {
  // PLACEHOLDER: replace with the API call.
  return files.map((file, i) => ({
    id: `new-${Date.now()}-${i}`,
    title: file.name,
    status: "Processing",
    pillars: [],
    createdBy: placeholderUser.name,
  }));
}