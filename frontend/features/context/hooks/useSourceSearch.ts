"use client";

import { useEffect, useState } from "react";
import { listSources } from "../services/contextService";
import type { Source } from "../types/source";

const SEARCH_DELAY_MS = 250;

/**
 * With no search text, returns the sources the page was rendered with. With search
 * text, asks the server, which matches titles, file names and note text. Results are
 * fetched again whenever the sources change, so a newly added note shows up in a search.
 */
export function useSourceSearch(projectId: number, query: string, sources: Source[]) {
  const needle = query.trim();
  const [results, setResults] = useState<Source[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!needle) return;
    let active = true;
    const timer = setTimeout(() => {
      listSources(projectId, needle)
        .then((items) => {
          if (!active) return;
          setResults(items);
          setError(null);
        })
        .catch(() => {
          if (active) setError("Search could not run. Try again.");
        });
    }, SEARCH_DELAY_MS);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [projectId, needle, sources]);

  if (!needle) return { visible: sources, error: null };
  return { visible: results ?? [], error };
}
