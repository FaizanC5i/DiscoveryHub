import "server-only";

import { cache } from "react";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { apiRequest, isApiError } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import { ROUTES } from "@/lib/constants";
import type { Project } from "@/types/project";

/**
 * Server-only reads for projects. They forward the visitor's cookies, so the
 * backend returns only that visitor's projects.
 *
 * Analogy: the archivist with the member's key card. The archivist fetches the
 * folder using the card the member holds, so the member sees only their own folders.
 */

/** Reads the visitor's cookies and builds the headers the backend expects. */
async function sessionHeaders(): Promise<HeadersInit> {
  const cookieStore = await cookies();
  return { Cookie: cookieStore.toString() };
}

/** Sends the visitor to sign in when the backend says the session is missing or expired. */
function handleSessionError(error: unknown): never {
  if (isApiError(error, "UNAUTHENTICATED") || isApiError(error, "SESSION_EXPIRED")) {
    redirect(ROUTES.login);
  }
  throw error;
}

/** The signed-in user's most recently updated projects. */
export async function listRecentProjects(limit: number): Promise<Project[]> {
  try {
    return await apiRequest<Project[]>(`${API_PATHS.projects.list}?limit=${limit}`, {
      method: "GET",
      headers: await sessionHeaders(),
      cache: "no-store",
      skipAuthRefresh: true,
    });
  } catch (error) {
    return handleSessionError(error);
  }
}

/**
 * Route helper for project pages. Turns the URL segment into a project, or shows the 404 page.
 *
 * Analogy: the receptionist who checks the room number on the booking before
 * sending a guest up. An unknown or invalid number gets the "not found" sign.
 */
export async function requireProjectForCurrentUser(projectIdParam: string): Promise<Project> {
  if (!/^\d+$/.test(projectIdParam)) {
    notFound();
  }
  const project = await getProjectForCurrentUser(Number(projectIdParam));
  if (project === null) {
    notFound();
  }
  return project;
}

/**
 * One project for the signed-in user, or null when it is missing or belongs to someone else.
 * Wrapped in cache() so the layout and the page share one backend call per request.
 */
export const getProjectForCurrentUser = cache(async (projectId: number): Promise<Project | null> => {
  try {
    return await apiRequest<Project>(API_PATHS.projects.detail(projectId), {
      method: "GET",
      headers: await sessionHeaders(),
      cache: "no-store",
      skipAuthRefresh: true,
    });
  } catch (error) {
    if (isApiError(error, "PROJECT_NOT_FOUND")) {
      return null;
    }
    return handleSessionError(error);
  }
});
