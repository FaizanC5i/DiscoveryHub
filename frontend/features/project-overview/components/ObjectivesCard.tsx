import { Badge } from "@/components/ui/Badge";
import { OverviewSection } from "./OverviewSection";
import { ComingSoonAction, YetToBeDone } from "./YetToBeDone";

export function ObjectivesCard() {
  return (
    <OverviewSection
      title="Objectives"
      badge={<Badge tone="brand">AI draft</Badge>}
      action={<ComingSoonAction label="Review →" />}
    >
      <YetToBeDone />
    </OverviewSection>
  );
}