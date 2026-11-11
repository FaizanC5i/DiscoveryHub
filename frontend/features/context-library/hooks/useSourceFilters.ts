"use client";

import { useMemo, useState } from "react";
import type { ContextSource, PillarId, SourceOrigin } from "../types/contextLibrary";

export function useSourceFilters(sources: ContextSource[]) {
  const [query, setQuery] = useState("");
  const [pillar, setPillar] = useState<PillarId | "all">("all");
  const [origin, setOrigin] = useState<SourceOrigin | "all">("all");

  const filteredSources = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return sources.filter(
      (source) =>
        (pillar === "all" || source.pillar === pillar) &&
        (origin === "all" || source.origin === origin) &&
        (needle === "" || source.name.toLowerCase().includes(needle)),
    );
  }, [sources, query, pillar, origin]);

  return { query, setQuery, pillar, setPillar, origin, setOrigin, filteredSources };
}