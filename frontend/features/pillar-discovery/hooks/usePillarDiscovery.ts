"use client";

import { useEffect, useState } from "react";
import { getDiscoveryOverview } from "@/features/discovery/services/discovery.service";
import type { DiscoveryOverview, PillarId } from "@/features/discovery/types/discovery.types";
import {
  getPillarDiscovery,
  uploadPhaseArtifact,
  uploadPillarSources,
} from "../services/pillar-discovery.service";
import type { PhaseId, PillarDiscovery } from "../types/pillar-discovery.types";

/**
 * Loads one pillar's discovery page, plus the project-wide discovery overview
 * that the context library uses for its progress box.
 */
export function usePillarDiscovery(projectId: string, pillarId: PillarId) {
  const [overview, setOverview] = useState<DiscoveryOverview | null>(null);
  const [pillar, setPillar] = useState<PillarDiscovery | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getDiscoveryOverview(projectId), getPillarDiscovery(projectId, pillarId)])
      .then(([overviewResult, pillarResult]) => {
        if (cancelled) return;
        setOverview(overviewResult);
        setPillar(pillarResult);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load this discovery area.");
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, pillarId, reloadKey]);

  function retry() {
    setError(null);
    setOverview(null);
    setPillar(null);
    setReloadKey((k) => k + 1);
  }

  async function uploadArtifact(phaseId: PhaseId, artifactId: string, file: File) {
    if (!pillar || !overview) return;
    const phase = pillar.phases.find((p) => p.id === phaseId);
    const artifact = phase?.artifacts.find((a) => a.id === artifactId);
    if (!phase || !artifact) return;

    const result = await uploadPhaseArtifact(projectId, pillarId, phase, artifact, file, overview.user.name);
    setPillar((current) =>
      current
        ? {
            ...current,
            phases: current.phases.map((p) =>
              p.id === phaseId
                ? { ...p, artifacts: p.artifacts.map((a) => (a.id === artifactId ? result.artifact : a)) }
                : p,
            ),
            relevantSources: [...current.relevantSources, result.source],
          }
        : current,
    );
  }

  async function addLibraryFiles(files: File[]) {
    if (!overview || files.length === 0) return;
    const added = await uploadPillarSources(projectId, pillarId, files, overview.user.name);
    setPillar((current) =>
      current ? { ...current, relevantSources: [...current.relevantSources, ...added] } : current,
    );
  }

  return { overview, pillar, error, retry, uploadArtifact, addLibraryFiles };
}