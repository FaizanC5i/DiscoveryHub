/**
 * Browser-side project calls: create and update.
 *
 * Analogy: the order window at the shop. Customers hand over a form, and the
 * clerk sends it to the back office (the API). Reading projects on the server is
 * in serverProjectService.ts, which forwards the visitor's cookies.
 */
import { apiRequest } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import type { Project, ProjectInput } from "@/types/project";

export function createProject(input: ProjectInput): Promise<Project> {
  return apiRequest<Project>(API_PATHS.projects.list, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateProject(projectId: number, input: ProjectInput): Promise<Project> {
  return apiRequest<Project>(API_PATHS.projects.detail(projectId), {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}
