import { Button } from "@/components/ui/Button";
import { OverviewSection } from "./OverviewSection";
import { YetToBeDone } from "./YetToBeDone";

const ARTIFACT_TYPES =
  "BRD · PRD · Problem Statement · User Personas · User Stories · Data Dictionary · Ontology · Solution Architecture · NFR";

export function ArtifactsCard() {
  return (
    <OverviewSection title="Work with artifacts">
      <p className="text-body-medium text-fg-secondary">{ARTIFACT_TYPES}</p>
      <YetToBeDone />
      <div className="flex flex-wrap gap-3">
        <Button disabled>Create Artifacts →</Button>
        <Button variant="outline" disabled>
          View previous artifacts
        </Button>
      </div>
    </OverviewSection>
  );
}