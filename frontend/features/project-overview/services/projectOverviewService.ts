import { mockProjectOverview } from "../data/mockProjectOverview";
import type { ProjectOverview } from "../types/projectOverview";

/** Returns mock data for now. Replace the body with the API call (lib/api/client) later. */
export async function getProjectOverview(_projectId: string): Promise<ProjectOverview> {
  return mockProjectOverview;
}