"use client";

import { useEffect, useState } from "react";
import { getUserDiscovery } from "../services/userDiscoveryService";

const POLL_MS = 15000;

/** How many proposed answers are waiting for review. Refreshes so background runs show up. */
export function usePendingProposalCount(projectId: number): number {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const overview = await getUserDiscovery(projectId);
        if (cancelled) return;
        setCount(overview.checkpoints.filter((card) => card.pending_proposal?.proposed_answer.trim()).length);
      } catch {
        // Keep the last known count when the request fails.
      }
    }

    void load();
    const timer = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [projectId]);

  return count;
}
