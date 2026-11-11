import { mockContextLibrary } from "../data/mockContextLibrary";
import type { ContextLibrary } from "../types/contextLibrary";

/** Returns mock data for now. Replace the body with the API call (lib/api/client) later. */
export async function getContextLibrary(_projectId: string): Promise<ContextLibrary> {
  return mockContextLibrary;
}