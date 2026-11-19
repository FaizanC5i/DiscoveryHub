"use client";

import { useState } from "react";
import { ContextLibraryWorkspace } from "@/features/context/components/ContextLibraryWorkspace";
import type { Source } from "@/features/context/types/source";
import { PageError, PageLoading } from "@/features/discovery/components/PageStatus";
import type { PillarId } from "@/features/discovery/types/discovery.types";
import { UserDiscoveryChecklist } from "@/features/user-discovery/components/UserDiscoveryChecklist";
import { usePillarDiscovery } from "../hooks/usePillarDiscovery";
import type { PhaseId } from "../types/pillar-discovery.types";
import { getPillarProgress } from "../utils/pillar-progress";
import { ChecklistCard } from "./ChecklistCard";
import { GuidedDesignThinking } from "./GuidedDesignThinking";
import { PillarSubNav } from "./PillarSubNav";
import { WorkflowNote } from "./WorkflowNote";

interface PillarDiscoveryViewProps {
  projectId: string;
  pillarId: PillarId;
  sources: Source[];
}

/** Full-screen pillar page (User Discovery). Uses the same context library as the other project pages. */
export function PillarDiscoveryView({ projectId, pillarId, sources }: PillarDiscoveryViewProps) {
  const { pillar, error, retry, uploadArtifact } = usePillarDiscovery(projectId, pillarId);
  // First phase starts expanded, as in the design. null = all collapsed.
  const [activePhaseId, setActivePhaseId] = useState<PhaseId | null>("EMPATHIZE");

  if (error) return <PageError message={error} onRetry={retry} />;
  if (!pillar) return <PageLoading label="Loading discovery…" />;

  const progress = getPillarProgress(pillar.questions);

  /** Open a phase and scroll to it (used by the tiles and by "Get help"). */
  function showPhase(phaseId: PhaseId) {
    setActivePhaseId(phaseId);
    requestAnimationFrame(() => {
      document.getElementById(`phase-${phaseId}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  return (
    <div className="flex flex-1 flex-col">
      <PillarSubNav projectId={projectId} title={pillar.name} />

      <main className="px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <ContextLibraryWorkspace projectId={Number(projectId)} sources={sources}>
          {pillarId === "USER" ? (
            <UserDiscoveryChecklist projectId={Number(projectId)} />
          ) : (
            <ChecklistCard
              title={`${pillar.name} checklist`}
              description={pillar.description}
              progress={progress}
              targetPercent={pillar.targetPercent}
              questions={pillar.questions}
              phases={pillar.phases}
              onGetHelp={showPhase}
            />
          )}

          <GuidedDesignThinking
            phases={pillar.phases}
            questions={pillar.questions}
            activePhaseId={activePhaseId}
            onSelectPhase={showPhase}
            onTogglePhase={(phaseId) => setActivePhaseId((current) => (current === phaseId ? null : phaseId))}
            onUploadArtifact={uploadArtifact}
          />

          <WorkflowNote />
        </ContextLibraryWorkspace>
      </main>
    </div>
  );
}
