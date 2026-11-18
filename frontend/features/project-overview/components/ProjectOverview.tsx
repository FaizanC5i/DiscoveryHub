"use client";

import { ContextLibraryWorkspace } from "@/features/context/components/ContextLibraryWorkspace";
import type { Source } from "@/features/context/types/source";
import { UserDiscoveryCard } from "@/features/user-discovery/components/UserDiscoveryCard";
import type { Project } from "@/types/project";
import { ArtifactsCard } from "./ArtifactsCard";
import { DiscoveryCard } from "./DiscoveryCard";
import { FeaturedDiscoverySection } from "./FeaturedDiscoverySection";
import { ProjectSummaryCard } from "./ProjectSummaryCard";

interface ProjectOverviewProps {
  project: Project;
  sources: Source[];
}

/** The overview content, beside the shared context library. */
export function ProjectOverview({ project, sources }: ProjectOverviewProps) {
  return (
    <ContextLibraryWorkspace projectId={project.id} sources={sources}>
      <ProjectSummaryCard project={project} />
      <UserDiscoveryCard projectId={project.id} />
      <FeaturedDiscoverySection projectId={project.id} />
      <DiscoveryCard />
      <ArtifactsCard />
    </ContextLibraryWorkspace>
  );
}
