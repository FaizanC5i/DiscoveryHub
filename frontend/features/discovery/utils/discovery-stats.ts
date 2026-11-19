import type { DiscoveryStats, Pillar } from "../types/discovery.types";

/** Whole-number percentage: 2 of 15 -> 13. */
export function toPercent(part: number, total: number): number {
  return total === 0 ? 0 : Math.round((part / total) * 100);
}

/** Project totals. Only checkpoints approved by a person count as verified. */
export function getDiscoveryStats(pillars: Pillar[]): DiscoveryStats {
  const verified = pillars.reduce((sum, p) => sum + p.verified, 0);
  const total = pillars.reduce((sum, p) => sum + p.total, 0);
  const gaps = pillars.flatMap((p) => p.gaps);

  return {
    verified,
    total,
    percent: toPercent(verified, total),
    unresolved: total - verified,
    criticalGaps: gaps.filter((g) => g.priority === "critical").length,
    noEvidence: gaps.filter((g) => g.status === "no-evidence").length,
    awaitingReview: gaps.filter((g) => g.status === "awaiting-review").length,
  };
}