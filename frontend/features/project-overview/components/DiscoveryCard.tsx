import { OverviewSection } from "./OverviewSection";
import { YetToBeDone } from "./YetToBeDone";

export function DiscoveryCard() {
  return (
    <OverviewSection
      title="Discovery"
      action={
        <span className="text-caption text-fg-muted">
          Readiness is based on reviewed evidence, not project status.
        </span>
      }
    >
      <YetToBeDone />
    </OverviewSection>
  );
}