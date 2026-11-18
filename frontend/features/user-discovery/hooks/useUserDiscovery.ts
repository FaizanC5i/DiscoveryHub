"use client";

import { useCallback, useEffect, useState } from "react";
import {
  approveProposal,
  getUserDiscovery,
  regenerateCheckpoint,
  startUserDiscoveryRun,
} from "../services/userDiscoveryService";
import type { UserDiscoveryOverview } from "../types/userDiscovery";

const POLL_MS = 3000;
const MAX_POLLS = 200;

function messageOf(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong. Please try again.";
}

export function useUserDiscovery(projectId: number) {
  const [overview, setOverview] = useState<UserDiscoveryOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [watching, setWatching] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const next = await getUserDiscovery(projectId);
      setOverview(next);
      setError(null);
      if (next.running) setWatching(true);
      return next;
    } catch (err) {
      setError(messageOf(err));
      return null;
    }
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  // Poll while a run is in progress. Two polls at minimum, so a run that has just
  // started is not mistaken for a finished one.
  useEffect(() => {
    if (!watching) return;
    let ticks = 0;
    const timer = setInterval(async () => {
      ticks += 1;
      const next = await load();
      if ((next && !next.running && ticks >= 2) || ticks >= MAX_POLLS) setWatching(false);
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [watching, load]);

  async function perform(action: () => Promise<unknown>, watchAfter: boolean): Promise<boolean> {
    setBusy(true);
    setError(null);
    try {
      await action();
      if (watchAfter) setWatching(true);
      await load();
      return true;
    } catch (err) {
      setError(messageOf(err));
      return false;
    } finally {
      setBusy(false);
    }
  }

  return {
    overview,
    error,
    busy,
    startRun: () => perform(() => startUserDiscoveryRun(projectId), true),
    regenerate: (checkpointId: number) =>
      perform(() => regenerateCheckpoint(projectId, checkpointId), true),
    approve: (proposalId: number, overrideText?: string) =>
      perform(() => approveProposal(projectId, proposalId, overrideText), false),
  };
}