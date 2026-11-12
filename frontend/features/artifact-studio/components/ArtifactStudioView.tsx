"use client";

import { useEffect, useState } from "react";
import { ContextLibrary } from "@/features/discovery/components/ContextLibrary";
import { DiscoveryHeader } from "@/features/discovery/components/DiscoveryHeader";
import { DiscoveryTabs } from "@/features/discovery/components/DiscoveryTabs";
import { PageError, PageLoading } from "@/features/discovery/components/PageStatus";
import { getDiscoveryOverview, uploadSourceFiles } from "@/features/discovery/services/discovery.service";
import type { DiscoveryOverview } from "@/features/discovery/types/discovery.types";
import { getDiscoveryStats } from "@/features/discovery/utils/discovery-stats";
import { getArtifactStudioData } from "../services/artifact-studio.service";
import type { ArtifactCode, ArtifactStudioData } from "../types/artifact-studio.types";
import { ArtifactTypePicker } from "./ArtifactTypePicker";
import { AvailableArtifacts } from "./AvailableArtifacts";
import { DraftConfigForm } from "./DraftConfigForm";
import { EvidenceReadiness } from "./EvidenceReadiness";

interface ArtifactStudioViewProps {
  projectId: string;
  /** From the URL, e.g. ?artifact=BRD when coming from "Generate BRD". */
  initialArtifact?: string;
}

/** The full Artifact Studio page. All data comes from the service files. */
export function ArtifactStudioView({ projectId, initialArtifact }: ArtifactStudioViewProps) {
  const [overview, setOverview] = useState<DiscoveryOverview | null>(null);
  const [studio, setStudio] = useState<ArtifactStudioData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedCode, setSelectedCode] = useState<ArtifactCode | null>(null);
  const [isLibraryOpen, setIsLibraryOpen] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getDiscoveryOverview(projectId), getArtifactStudioData(projectId)])
      .then(([overviewResult, studioResult]) => {
        if (cancelled) return;
        setOverview(overviewResult);
        setStudio(studioResult);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load Artifact Studio.");
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, reloadKey]);

  function retry() {
    setError(null);
    setOverview(null);
    setStudio(null);
    setReloadKey((k) => k + 1);
  }

  async function handleAddFiles(files: File[]) {
    const added = await uploadSourceFiles(projectId, files);
    setOverview((current) => (current ? { ...current, sources: [...current.sources, ...added] } : current));
  }

  if (error) return <PageError message={error} onRetry={retry} />;
  if (!overview || !studio) return <PageLoading label="Loading Artifact Studio…" />;

  // Selected type: the user's pick, else ?artifact= from the URL, else the first type.
  const selected =
    studio.artifactTypes.find((t) => t.code === selectedCode) ??
    studio.artifactTypes.find((t) => t.code === initialArtifact) ??
    studio.artifactTypes[0]!;
  const stats = getDiscoveryStats(overview.pillars);

  return (
    <div className="flex min-h-dvh flex-col bg-(--color-bg-default-secondary) text-(--color-text-default-primary)">
      <DiscoveryHeader projectName={overview.project.name} userName={overview.user.name} />

      <DiscoveryTabs
        projectId={projectId}
        activeTab="studio"
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
          <AvailableArtifacts projectId={projectId} artifacts={studio.availableArtifacts} types={studio.artifactTypes} />

          <div>
            <h1 className="m-0 mb-(--space-2) text-(length:--font-size-heading-4) leading-(--line-height-heading-4) font-semibold">
              Turn context into a useful working draft
            </h1>
            <p className="m-0 max-w-[72ch] font-(family-name:--font-family-secondary) text-(length:--font-size-body-large) leading-(--line-height-body-large) text-(--color-text-default-subtle)">
              Select an artifact, review how ready your sources are, and choose whether to resolve gaps first or
              knowingly generate an incomplete draft.
            </p>
          </div>

          <ArtifactTypePicker types={studio.artifactTypes} selected={selected.code} onSelect={setSelectedCode} />

          <div className="grid grid-cols-1 items-start gap-(--space-5) lg:grid-cols-2">
            <EvidenceReadiness
              projectId={projectId}
              artifactName={selected.name}
              readiness={studio.readiness[selected.code]}
            />
            <DraftConfigForm
              key={selected.code}
              projectId={projectId}
              projectName={overview.project.name}
              artifact={selected}
              audiences={studio.audiences}
               readiness={studio.readiness[selected.code]}
            />
          </div>

          <p className="m-0 rounded-(--radius-lg) border border-dashed border-(--color-border-default-primary) bg-(--color-bg-default-primary) p-(--space-4) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-secondary)">
            <strong className="font-semibold text-(--color-text-default-primary)">Library reads and generation.</strong>{" "}
            Studio reads the same project library visible at right. Generating snapshots the selected sources and the
            current coverage. Opening a draft does not change discovery counts.
          </p>
        </main>

        {isLibraryOpen && (
          <ContextLibrary
            pillars={overview.pillars}
            stats={stats}
            sources={overview.sources}
            onAddFiles={handleAddFiles}
            onClose={() => setIsLibraryOpen(false)}
          />
        )}
      </div>
    </div>
  );
}