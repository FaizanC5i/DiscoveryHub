import type { Metadata } from "next";
import { ProjectSummaryCard } from "@/features/project-overview/components/ProjectSummaryCard";
import { SourcesCard } from "@/features/project-overview/components/SourcesCard";
import { requireProjectForCurrentUser } from "@/features/projects/services/serverProjectService";

export const metadata: Metadata = {
  title: "Project overview",
};

export const instant = false;

/**
 * Overview of one project. The data is fetched on the server with the visitor's
 * cookies, so only the owner can see it. A project that does not belong to them
 * shows the 404 page, the same as a project that does not exist.
 */
export default async function ProjectOverviewPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await requireProjectForCurrentUser(projectId);

  return (
    <div className="flex flex-col gap-6">
      <ProjectSummaryCard project={project} />
      <SourcesCard />
    </div>
  );
}
