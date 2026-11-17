"use client";

import { useCallback, useEffect, useState } from "react";
import { listSources } from "../services/contextService";
import type { Source } from "../types/source";
import { isWorking } from "../utils/sourceFilters";

const POLL_INTERVAL_MS = 3000;

interface LiveList {
  /** The server list this overlay was built on. A new server list replaces the overlay. */
  base: Source[];
  items: Source[];
}

/**
 * Returns the project's sources, kept current while any of them is still processing or
 * being mapped. Sources the user just saved are added at once, so they show their
 * processing state from the start. Polling then replaces them with the server's state.
 */
export function useLiveSources(projectId: number, serverSources: Source[]) {
  const [live, setLive] = useState<LiveList | null>(null);
  const current = live && live.base === serverSources ? live.items : serverSources;
  const working = current.some(isWorking);

  useEffect(() => {
    if (!working) return;
    let active = true;
    const timer = setInterval(() => {
      listSources(projectId, "")
        .then((items) => {
          if (active) setLive({ base: serverSources, items });
        })
        .catch(() => undefined);
    }, POLL_INTERVAL_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [working, projectId, serverSources]);

  const addSaved = useCallback(
    (saved: Source[]) => {
      if (saved.length === 0) return;
      const savedIds = new Set(saved.map((source) => source.id));
      setLive({
        base: serverSources,
        items: [...saved, ...current.filter((source) => !savedIds.has(source.id))],
      });
    },
    [current, serverSources],
  );

  return { sources: current, addSaved };
}
