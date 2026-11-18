import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { YetToBeDone } from "@/components/ui/YetToBeDone";
import type { CheckpointCard } from "@/features/user-discovery/types/userDiscovery";
import { statusOf } from "@/features/user-discovery/utils/cardStatus";
import { OverviewSection } from "./OverviewSection";

interface EndUsersCardProps {
  card: CheckpointCard | null;
  onReview: () => void;
}

export function EndUsersCard({ card, onReview }: EndUsersCardProps) {
  const status = card ? statusOf(card) : null;
  const displayText =
    card?.current_answer?.text ?? card?.pending_proposal?.proposed_answer?.trim() ?? null;

  return (
    <OverviewSection
      title="End users"
      badge={status ? <Badge tone={status.tone}>{status.label}</Badge> : null}
      action={
        <Button size="sm" variant="outline" onClick={onReview} disabled={!card}>
          Review
        </Button>
      }
    >
      {displayText ? (
        <p className="whitespace-pre-line text-body-medium text-fg">{displayText}</p>
      ) : (
        <YetToBeDone />
      )}
    </OverviewSection>
  );
}
