import type { DiscoveryStats, Pillar } from "../types/discovery.types";

/** Whole-number percentage: 2 of 15 -> 13. */
export function toPercent(part: number, total: number): number {
  return total === 0 ? 0 : Math.round((part / total) * 100);
}

/** Pillars with live data. The headline counts only these, so placeholder pillars do not move it. */
const COUNTED_PILLARS: Pillar["id"][] = ["USER"];

/** Project totals. Only checkpoints approved by a person count as verified. */
export function getDiscoveryStats(pillars: Pillar[]): DiscoveryStats {
  const counted = pillars.filter((p) => COUNTED_PILLARS.includes(p.id));
  const verified = counted.reduce((sum, p) => sum + p.verified, 0);
  const total = counted.reduce((sum, p) => sum + p.total, 0);
  const gaps = counted.flatMap((p) => p.gaps);

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