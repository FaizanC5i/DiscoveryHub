"use client";

import { useEffect, useState } from "react";
import { ContextLibraryWorkspace } from "@/features/context/components/ContextLibraryWorkspace";
import type { Source } from "@/features/context/types/source";
import { PageError, PageLoading } from "@/features/discovery/components/PageStatus";
import { useDiscoveryOverview } from "@/features/discovery/hooks/useDiscoveryOverview";
import { getArtifactStudioData } from "../services/artifact-studio.service";
import type { ArtifactCode, ArtifactStudioData } from "../types/artifact-studio.types";
import { ArtifactTypePicker } from "./ArtifactTypePicker";
import { AvailableArtifacts } from "./AvailableArtifacts";
import { DraftConfigForm } from "./DraftConfigForm";
import { EvidenceReadiness } from "./EvidenceReadiness";

interface ArtifactStudioViewProps {
  projectId: string;
  sources: Source[];
  /** From the URL, e.g. ?artifact=BRD when coming from "Generate BRD". */
  initialArtifact?: string;
}

/** The Artifact Studio tab. The project header and tab bar come from the project layout. */
export function ArtifactStudioView({ projectId, sources, initialArtifact }: ArtifactStudioViewProps) {
  const discovery = useDiscoveryOverview(projectId);
  const [studio, setStudio] = useState<ArtifactStudioData | null>(null);
  const [studioError, setStudioError] = useState<string | null>(null);
  const [studioReloadKey, setStudioReloadKey] = useState(0);
  const [selectedCode, setSelectedCode] = useState<ArtifactCode | null>(null);

  useEffect(() => {
    let cancelled = false;
    getArtifactStudioData(projectId)
      .then((result) => {
        if (!cancelled) setStudio(result);
      })
      .catch((e: unknown) => {
        if (!cancelled) setStudioError(e instanceof Error ? e.message : "Could not load Artifact Studio.");
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, studioReloadKey]);

  const { overview, retry: retryDiscovery } = discovery;
  const error = discovery.error ?? studioError;

  function retry() {
    setStudioError(null);
    setStudio(null);
    setStudioReloadKey((k) => k + 1);
    retryDiscovery();
  }

  if (error) return <PageError message={error} onRetry={retry} />;
  if (!overview || !studio) return <PageLoading label="Loading Artifact Studio…" />;

  // Selected type: the user's pick, else ?artifact= from the URL, else the first type.
  const selected =
    studio.artifactTypes.find((t) => t.code === selectedCode) ??
    studio.artifactTypes.find((t) => t.code === initialArtifact) ??
    studio.artifactTypes[0]!;

  return (
    <ContextLibraryWorkspace projectId={Number(projectId)} sources={sources}>
      <AvailableArtifacts projectId={projectId} artifacts={studio.availableArtifacts} types={studio.artifactTypes} />

      <div>
        <h1 className="m-0 mb-(--space-2) text-(length:--font-size-heading-4) leading-(--line-height-heading-4) font-semibold">
          Turn context into a useful working draft
        </h1>
        <p className="m-0 max-w-[72ch] font-(family-name:--font-family-secondary) text-(length:--font-size-body-large) leading-(--line-height-body-large) text-(--color-text-default-subtle)">
          Select an artifact, review how ready your sources are, and choose whether to resolve gaps first or knowingly
          generate an incomplete draft.
        </p>
      </div>

      <ArtifactTypePicker types={studio.artifactTypes} selected={selected.code} onSelect={setSelectedCode} />

      <div className="grid grid-cols-1 items-start gap-(--space-5) lg:grid-cols-2">
        <EvidenceReadiness projectId={projectId} artifactName={selected.name} readiness={studio.readiness[selected.code]} />
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
    </ContextLibraryWorkspace>
  );
}
