"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { ContextLibrary } from "@/features/context/components/ContextLibrary";
import type { Source } from "@/features/context/types/source";
import { cn } from "@/lib/cn";
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

/**
 * The overview: project header and content sections on the left, the context
 * library on the right. The library can be hidden to give the content full width.
 */
export function ProjectOverview({ project, sources }: ProjectOverviewProps) {
  const [isLibraryOpen, setIsLibraryOpen] = useState(true);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={() => setIsLibraryOpen((open) => !open)}>
          {isLibraryOpen ? "Hide context library" : "Show context library"}
        </Button>
      </div>

      <div
        className={cn(
          "grid gap-6",
          isLibraryOpen && "lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start",
        )}
      >
        <div className="flex min-w-0 flex-col gap-6">
          <ProjectSummaryCard project={project} />
          <ProblemStatementCard />
          <div className="grid gap-6 md:grid-cols-2">
            <ObjectivesCard />
            <StakeholdersCard />
          </div>
          <DiscoveryCard />
          <ArtifactsCard />
        </div>

        {isLibraryOpen ? (
          <div className="lg:sticky lg:top-6">
            <ContextLibrary
              projectId={project.id}
              sources={sources}
              onHide={() => setIsLibraryOpen(false)}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}