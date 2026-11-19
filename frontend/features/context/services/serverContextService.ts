import "server-only";

import { apiRequest } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import { handleSessionError, sessionHeaders } from "@/lib/api/serverSession";
import type { Source } from "../types/source";

/**
 * The project's documents for the signed-in visitor. Runs on the server, so the
 * list is in the first HTML the browser receives.
 */
export async function listSourcesForCurrentUser(projectId: number): Promise<Source[]> {
  try {
    return await apiRequest<Source[]>(API_PATHS.sources.list(projectId), {
      method: "GET",
      headers: await sessionHeaders(),
      cache: "no-store",
      skipAuthRefresh: true,
    });
  } catch (error) {
    return handleSessionError(error);
  }
}