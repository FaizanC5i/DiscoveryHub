import { listRecentProjects } from "@/features/projects/services/serverProjectService";
import { QUICK_ACCESS_ITEMS } from "../data/quickAccessItems";
import type { DashboardData } from "../types/dashboard";

/** How many projects the dashboard shows before "see all" is needed. */
const RECENT_PROJECT_LIMIT = 5;

/**
 * Dashboard data boundary. Projects come from the API for the signed-in user.
 * Quick-access cards are static, so they come from a local list.
 */
export async function getDashboardData(): Promise<DashboardData> {
  const projects = await listRecentProjects(RECENT_PROJECT_LIMIT);
  return { projects, quickAccess: QUICK_ACCESS_ITEMS };
}
