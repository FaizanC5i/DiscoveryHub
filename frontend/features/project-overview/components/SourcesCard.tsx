import { Badge } from "@/components/ui/Badge";
import { SectionCard } from "@/components/ui/SectionCard";

/**
 * Placeholder for project documents. It is disabled and makes no API calls.
 * Upload will be added in a later release, and this card is where it will go.
 */
export function SourcesCard() {
  return (
    <div aria-disabled="true">
      <SectionCard title="Sources" badge={<Badge tone="neutral">Coming soon</Badge>}>
        <p className="text-body-medium text-fg-disabled">Document upload coming soon.</p>
      </SectionCard>
    </div>
  );
}
