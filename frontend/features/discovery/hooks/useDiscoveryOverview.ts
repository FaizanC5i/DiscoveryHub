"use client";

import { useEffect, useState } from "react";
import { getDiscoveryOverview, uploadSourceFiles } from "../services/discovery.service";
import type { DiscoveryOverview } from "../types/discovery.types";

/** Loads a project's discovery overview and keeps its source list current after uploads. */
export function useDiscoveryOverview(projectId: string) {
  const [overview, setOverview] = useState<DiscoveryOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    getDiscoveryOverview(projectId)
      .then((result) => {
        if (!cancelled) setOverview(result);
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
    setOverview(null);
    setReloadKey((k) => k + 1);
  }

  async function addSourceFiles(files: File[]) {
    const added = await uploadSourceFiles(projectId, files);
    setOverview((current) => (current ? { ...current, sources: [...current.sources, ...added] } : current));
  }

  return { overview, error, retry, addSourceFiles };
}
