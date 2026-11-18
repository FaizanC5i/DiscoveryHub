import type { CheckpointCard } from "../types/userDiscovery";

export interface StatusView {
  label: string;
  tone: "success" | "brand" | "neutral" | "warning";
}

export function statusOf(card: CheckpointCard): StatusView | null {
  if (card.current_answer?.status === "APPROVED") return { label: "Approved", tone: "success" };
  if (card.pending_proposal?.agent_status === "Needs Clarification") {
    return { label: "Clarification needed", tone: "warning" };
  }
  if (card.pending_proposal) return { label: "Not reviewed", tone: "brand" };
  return null;
}
