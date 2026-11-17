import type { CheckpointCard } from "../types/userDiscovery";

export interface StatusView {
  label: string;
  tone: "success" | "brand" | "neutral";
}

export function statusOf(card: CheckpointCard): StatusView {
  if (card.current_answer?.status === "APPROVED") return { label: "Approved", tone: "success" };
  if (card.pending_proposal) {
    return card.pending_proposal.proposed_answer.trim()
      ? { label: "Ready to review", tone: "brand" }
      : { label: "Needs clarification", tone: "neutral" };
  }
  if (card.chunk_count === 0) return { label: "No evidence", tone: "neutral" };
  return { label: "Not generated", tone: "neutral" };
}