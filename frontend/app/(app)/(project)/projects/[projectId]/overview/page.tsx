import type { Metadata } from "next";
import { listSourcesForCurrentUser } from "@/features/context/services/serverContextService";
import { ProjectOverview } from "@/features/project-overview/components/ProjectOverview";
import { requireProjectForCurrentUser } from "@/features/projects/services/serverProjectService";

export const metadata: Metadata = {
  title: "Project overview",
};

export const instant = false;

/**
 * Server page: fetches the project and its sources with the visitor's cookies,
 * then hands them to the client overview, which manages the panel and notes.
 */
export default async function ProjectOverviewPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await requireProjectForCurrentUser(projectId);
  const sources = await listSourcesForCurrentUser(project.id);

  return <ProjectOverview project={project} sources={sources} />;
}