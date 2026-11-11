import type { Metadata } from "next";
import { ArtifactsCard } from "@/features/project-overview/components/ArtifactsCard";
import { DiscoveryReadinessCard } from "@/features/project-overview/components/DiscoveryReadinessCard";
import { ObjectivesCard } from "@/features/project-overview/components/ObjectivesCard";
import { ProblemStatementCard } from "@/features/project-overview/components/ProblemStatementCard";
import { ProjectSummaryCard } from "@/features/project-overview/components/ProjectSummaryCard";
import { StakeholdersCard } from "@/features/project-overview/components/StakeholdersCard";
import { getProjectOverview } from "@/features/project-overview/services/projectOverviewService";

export const metadata: Metadata = {
  title: "Project overview",
};

export default async function ProjectOverviewPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const { summary, problemStatement, objectives, stakeholders, discovery, artifacts } =
    await getProjectOverview(projectId);

  const discoveryHref = `/projects/${projectId}/discovery`;
  const studioHref = `/projects/${projectId}/studio`;

  return (
    <div className="flex flex-col gap-6">
      <ProjectSummaryCard summary={summary} />
      <ProblemStatementCard statement={problemStatement} reviewHref={discoveryHref} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ObjectivesCard {...objectives} reviewHref={discoveryHref} />
        <StakeholdersCard {...stakeholders} reviewHref={discoveryHref} />
      </div>
      <DiscoveryReadinessCard readiness={discovery} gapsHref={discoveryHref} />
      <ArtifactsCard
        draftCount={artifacts.draftCount}
        artifacts={artifacts.available}
        studioHref={studioHref}
      />
    </div>
  );
}