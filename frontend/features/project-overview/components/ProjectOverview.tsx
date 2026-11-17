"use client";

import { ContextLibraryWorkspace } from "@/features/context/components/ContextLibraryWorkspace";
import type { Source } from "@/features/context/types/source";
import type { Project } from "@/types/project";
import { ArtifactsCard } from "./ArtifactsCard";
import { DiscoveryCard } from "./DiscoveryCard";
import { ObjectivesCard } from "./ObjectivesCard";
import { ProblemStatementCard } from "./ProblemStatementCard";
import { ProjectSummaryCard } from "./ProjectSummaryCard";
import { StakeholdersCard } from "./StakeholdersCard";

interface ProjectOverviewProps {
  project: Project;
  sources: Source[];
}

/** The overview content, beside the shared context library. */
export function ProjectOverview({ project, sources }: ProjectOverviewProps) {
  return (
    <ContextLibraryWorkspace projectId={project.id} sources={sources}>
      <ProjectSummaryCard project={project} />
      <ProblemStatementCard />
      <div className="grid gap-6 md:grid-cols-2">
        <ObjectivesCard />
        <StakeholdersCard />
      </div>
      <DiscoveryCard />
      <ArtifactsCard />
    </ContextLibraryWorkspace>
  );
}
