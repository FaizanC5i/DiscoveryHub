import { OverviewSection } from "./OverviewSection";
import { ComingSoonAction, YetToBeDone } from "./YetToBeDone";

export function StakeholdersCard() {
  return (
    <OverviewSection title="Stakeholders" action={<ComingSoonAction label="Review →" />}>
      <YetToBeDone />
    </OverviewSection>
  );
}