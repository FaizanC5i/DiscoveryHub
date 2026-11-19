import type { PillarId } from "@/features/discovery/types/discovery.types";

/** URL slug <-> pillar id. The Discovery Hub links to /discovery/user, /discovery/data, /discovery/tech. */
const SLUG_TO_PILLAR: Record<string, PillarId> = {
  user: "USER",
  data: "DATA",
  tech: "TECH",
};

export function pillarIdFromSlug(slug: string): PillarId | null {
  return SLUG_TO_PILLAR[slug.toLowerCase()] ?? null;
}