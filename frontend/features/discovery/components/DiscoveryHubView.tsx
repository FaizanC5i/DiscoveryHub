"use client";

import { useEffect, useState } from "react";
import { getDiscoveryOverview, uploadSourceFiles } from "../services/discovery.service";
import type { DiscoveryOverview } from "../types/discovery.types";
import { getDiscoveryStats } from "../utils/discovery-stats";
import { ContextLibrary } from "./ContextLibrary";
import { DiscoveryHeader } from "./DiscoveryHeader";
import { DiscoverySummary } from "./DiscoverySummary";
import { DiscoveryTabs } from "./DiscoveryTabs";
import { PageError, PageLoading } from "./PageStatus";
import { PillarCard } from "./PillarCard";

/** The full Discovery Hub page. All data comes from discovery.service.ts. */
export function DiscoveryHubView({ projectId }: { projectId: string }) {
  const [data, setData] = useState<DiscoveryOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [isLibraryOpen, setIsLibraryOpen] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getDiscoveryOverview(projectId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load discovery data.");
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, reloadKey]);

  function retry() {
    setError(null);
    setData(null);
    setReloadKey((k) => k + 1);
  }

  async function handleAddFiles(files: File[]) {
    const added = await uploadSourceFiles(projectId, files);
    setData((current) => (current ? { ...current, sources: [...current.sources, ...added] } : current));
  }

  if (error) return <PageError message={error} onRetry={retry} />;
  if (!data) return <PageLoading label="Loading discovery…" />;

  const stats = getDiscoveryStats(data.pillars);

  return (
    <div className="flex min-h-dvh flex-col bg-(--color-bg-default-secondary) text-(--color-text-default-primary)">
      <DiscoveryHeader projectName={data.project.name} userName={data.user.name} />

      <DiscoveryTabs
        projectId={projectId}
        activeTab="discovery"
        isLibraryOpen={isLibraryOpen}
        onToggleLibrary={() => setIsLibraryOpen((open) => !open)}
      />

      {/* Library panel is 320px wide (--space-64 + --space-16) */}
      <div
        className={`grid flex-1 grid-cols-1 ${
          isLibraryOpen ? "lg:grid-cols-[minmax(0,1fr)_calc(var(--space-64)+var(--space-16))]" : ""
        }`}
      >
        <main className="flex min-w-0 flex-col gap-(--space-6) p-(--space-4) lg:p-(--space-7)">
          <DiscoverySummary projectId={projectId} stats={stats} targetPercent={data.targetPercent} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-(--space-5)">
            {data.pillars.map((pillar) => (
              <PillarCard key={pillar.id} projectId={projectId} pillar={pillar} />
            ))}
          </div>
        </main>

        {isLibraryOpen && (
          <ContextLibrary
            pillars={data.pillars}
            stats={stats}
            sources={data.sources}
            onAddFiles={handleAddFiles}
            onClose={() => setIsLibraryOpen(false)}
          />
        )}
      </div>
    </div>
  );
}