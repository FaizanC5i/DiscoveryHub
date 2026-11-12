"use client";

import { useDiscoveryOverview } from "../hooks/useDiscoveryOverview";
import { getDiscoveryStats } from "../utils/discovery-stats";
import { DiscoverySummary } from "./DiscoverySummary";
import { LibraryWorkspace } from "./LibraryWorkspace";
import { PageError, PageLoading } from "./PageStatus";
import { PillarCard } from "./PillarCard";

/** The Discovery Hub tab. The project header and tab bar come from the project layout. */
export function DiscoveryHubView({ projectId }: { projectId: string }) {
  const { overview, error, retry, addSourceFiles } = useDiscoveryOverview(projectId);

  if (error) return <PageError message={error} onRetry={retry} />;
  if (!overview) return <PageLoading label="Loading discovery…" />;

  const stats = getDiscoveryStats(overview.pillars);

  return (
    <LibraryWorkspace
      pillars={overview.pillars}
      stats={stats}
      sources={overview.sources}
      onAddFiles={addSourceFiles}
    >
      <DiscoverySummary projectId={projectId} stats={stats} targetPercent={overview.targetPercent} />

      <div className="grid grid-cols-1 gap-(--space-5) lg:grid-cols-3">
        {overview.pillars.map((pillar) => (
          <PillarCard key={pillar.id} projectId={projectId} pillar={pillar} />
        ))}
      </div>
    </LibraryWorkspace>
  );
}
