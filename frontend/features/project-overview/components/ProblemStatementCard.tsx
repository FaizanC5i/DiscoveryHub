import { OverviewSection } from "./OverviewSection";
import { ComingSoonAction, YetToBeDone } from "./YetToBeDone";

export function ProblemStatementCard() {
  return (
    <OverviewSection title="Problem statement" action={<ComingSoonAction label="Review →" />}>
      <YetToBeDone />
    </OverviewSection>
  );
}