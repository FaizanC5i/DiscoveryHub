/**
 * Discovery data access. Components never read data directly; they call these functions.
 *
 * BACKEND INTEGRATION: only the bodies of these functions change.
 * Use the same API helper your dashboard services use (it sends the login cookies).
 * Keep the return types the same and nothing else in the app needs to change.
 */
import { FEATURED } from "@/features/user-discovery/constants/featuredCheckpoints";
import { getUserDiscovery } from "@/features/user-discovery/services/userDiscoveryService";
import type { CheckpointCard } from "@/features/user-discovery/types/userDiscovery";
import {
  placeholderPillars,
  placeholderProject,
  placeholderSources,
  placeholderUser,
  TARGET_PERCENT,
} from "../data/placeholder-data";
import type { DiscoveryOverview, Gap, Pillar } from "../types/discovery.types";

const FEATURED_CODES = new Set<string>(Object.values(FEATURED));

/**
 * The User Discovery pillar, counted the same way as the User Discovery checklist: the featured
 * checkpoints are left out, a checkpoint is verified when its answer is approved, and an open
 * checkpoint with no evidence is a critical gap.
 */
function userPillar(cards: CheckpointCard[]): Pillar {
  const inScope = cards.filter((card) => !FEATURED_CODES.has(card.checkpoint.code));
  const open = inScope.filter((card) => card.current_answer?.status !== "APPROVED");

  const gaps: Gap[] = open.map((card) => ({
    id: card.checkpoint.code,
    question: card.checkpoint.question,
    whyItMatters:
      card.pending_proposal?.missing_information[0] ??
      (card.chunk_count === 0 ? "No evidence in your library yet." : "Answer not generated yet."),
    source: card.checkpoint.name,
    priority: card.chunk_count === 0 ? "critical" : "recommended",
    status: card.chunk_count === 0 ? "no-evidence" : "awaiting-review",
  }));

  return {
    id: "USER",
    name: "User Discovery",
    shortName: "User",
    description: "Who the people are, how they work, what frustrates them and what they need.",
    verified: inScope.length - open.length,
    total: inScope.length,
    gaps,
  };
}

/**
 * Project, user, pillars with gaps, and context sources.
 * The User Discovery pillar comes from GET /api/projects/{projectId}/user-discovery.
 */
export async function getDiscoveryOverview(projectId: string): Promise<DiscoveryOverview> {
  const overview = await getUserDiscovery(Number(projectId));
  return {
    project: { id: projectId, name: placeholderProject.name },
    user: placeholderUser,
    targetPercent: TARGET_PERCENT,
    pillars: [
      userPillar(overview.checkpoints),
      ...placeholderPillars.filter((pillar) => pillar.id !== "USER"),
    ],
    sources: placeholderSources,
  };
}
