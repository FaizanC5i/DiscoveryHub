"use client";

import { useState } from "react";
import { PageError, PageLoading } from "@/features/discovery/components/PageStatus";
import type { PillarId } from "@/features/discovery/types/discovery.types";
import { getDiscoveryStats } from "@/features/discovery/utils/discovery-stats";
import { usePillarDiscovery } from "../hooks/usePillarDiscovery";
import type { PhaseId } from "../types/pillar-discovery.types";
import { getPillarProgress } from "../utils/pillar-progress";
import { ChecklistCard } from "./ChecklistCard";
import { GuidedDesignThinking } from "./GuidedDesignThinking";
import { PillarContextLibrary } from "./PillarContextLibrary";
import { PillarSubNav } from "./PillarSubNav";
import { WorkflowNote } from "./WorkflowNote";

interface PillarDiscoveryViewProps {
  projectId: string;
  pillarId: PillarId;
}

/** Full-screen pillar page (User Discovery). All data comes from pillar-discovery.service.ts. */
export function PillarDiscoveryView({ projectId, pillarId }: PillarDiscoveryViewProps) {
  const { overview, pillar, error, retry, uploadArtifact, addLibraryFiles } = usePillarDiscovery(projectId, pillarId);
  const [isLibraryOpen, setIsLibraryOpen] = useState(true);
  // First phase starts expanded, as in the design. null = all collapsed.
  const [activePhaseId, setActivePhaseId] = useState<PhaseId | null>("EMPATHIZE");

  if (error) return <PageError message={error} onRetry={retry} />;
  if (!overview || !pillar) return <PageLoading label="Loading discovery…" />;

  const progress = getPillarProgress(pillar.questions);
  const stats = getDiscoveryStats(overview.pillars);

  /** Open a phase and scroll to it (used by the tiles and by "Get help"). */
  function showPhase(phaseId: PhaseId) {
    setActivePhaseId(phaseId);
    requestAnimationFrame(() => {
      document.getElementById(`phase-${phaseId}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  return (
    <div className="flex flex-1 flex-col">
      <PillarSubNav
        projectId={projectId}
        title={pillar.name}
        isLibraryOpen={isLibraryOpen}
        onToggleLibrary={() => setIsLibraryOpen((open) => !open)}
      />

      <div className={isLibraryOpen ? "grid flex-1 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_auto]" : "flex flex-1"}>
        <main className="flex min-w-0 flex-1 flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <ChecklistCard
            title={`${pillar.name} checklist`}
            description={pillar.description}
            progress={progress}
            targetPercent={pillar.targetPercent}
            questions={pillar.questions}
            phases={pillar.phases}
            onGetHelp={showPhase}
          />

          <GuidedDesignThinking
            phases={pillar.phases}
            questions={pillar.questions}
            activePhaseId={activePhaseId}
            onSelectPhase={showPhase}
            onTogglePhase={(phaseId) => setActivePhaseId((current) => (current === phaseId ? null : phaseId))}
            onUploadArtifact={uploadArtifact}
          />

          <WorkflowNote />
        </main>

        {isLibraryOpen ? (
          <PillarContextLibrary
            pillarId={pillarId}
            pillarName={pillar.name}
            pillars={overview.pillars}
            stats={stats}
            sources={pillar.relevantSources}
            onAddFiles={addLibraryFiles}
          />
        ) : null}
      </div>
    </div>
  );
}