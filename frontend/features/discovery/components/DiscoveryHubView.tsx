"use client";

import { ContextLibraryWorkspace } from "@/features/context/components/ContextLibraryWorkspace";
import type { Source } from "@/features/context/types/source";
import { useDiscoveryOverview } from "../hooks/useDiscoveryOverview";
import { getDiscoveryStats } from "../utils/discovery-stats";
import { DiscoverySummary } from "./DiscoverySummary";
import { PageError, PageLoading } from "./PageStatus";
import { PillarCard } from "./PillarCard";

interface DiscoveryHubViewProps {
  projectId: string;
  sources: Source[];
}

/** The Discovery Hub tab. The project header and tab bar come from the project layout. */
export function DiscoveryHubView({ projectId, sources }: DiscoveryHubViewProps) {
  const { overview, error, retry } = useDiscoveryOverview(projectId);

  if (error) return <PageError message={error} onRetry={retry} />;
  if (!overview) return <PageLoading label="Loading discovery…" />;

  const stats = getDiscoveryStats(overview.pillars);

  return (
    <ContextLibraryWorkspace projectId={Number(projectId)} sources={sources}>
      <DiscoverySummary projectId={projectId} stats={stats} targetPercent={overview.targetPercent} />

      <div className="grid grid-cols-1 gap-(--space-5) lg:grid-cols-3">
        {overview.pillars.map((pillar) => (
          <PillarCard key={pillar.id} projectId={projectId} pillar={pillar} />
        ))}
      </div>
    </ContextLibraryWorkspace>
  );
}
