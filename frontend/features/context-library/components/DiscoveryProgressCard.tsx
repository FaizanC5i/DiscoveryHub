import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { PILLAR_LABELS } from "../constants";
import type { DiscoveryProgress } from "../types/contextLibrary";

export function DiscoveryProgressCard({ progress }: { progress: DiscoveryProgress }) {
  const { percentComplete, reviewed, total, pillars, unresolved, awaitingReview } = progress;

  return (
    <Card className="flex flex-col gap-3 p-4">
      <h3 className="text-body-large font-semibold text-fg">
        Discovery · {percentComplete}% complete · {reviewed}/{total} reviewed
      </h3>

      <ul className="flex flex-col gap-2">
        {pillars.map((pillar) => (
          <li key={pillar.id} className="flex items-center gap-3 text-body-small">
            <span className="w-10 text-fg">{PILLAR_LABELS[pillar.id]}</span>
            <ProgressBar
              value={(pillar.reviewed / pillar.total) * 100}
              label={`${PILLAR_LABELS[pillar.id]} pillar progress`}
              className="flex-1"
            />
            <span className="text-caption text-fg-muted">
              {pillar.reviewed}/{pillar.total} reviewed
            </span>
          </li>
        ))}
      </ul>

      <p className="text-caption text-fg-muted">
        {unresolved} unresolved · {awaitingReview} awaiting review
      </p>
    </Card>
  );
}