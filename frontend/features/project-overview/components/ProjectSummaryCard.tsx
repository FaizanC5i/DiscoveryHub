import { PencilIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { formatProjectDate } from "../utils/formatProjectDate";
import type { ProjectSummary } from "../types/projectOverview";

interface ProjectSummaryCardProps {
  summary: ProjectSummary;
}

export function ProjectSummaryCard({ summary }: ProjectSummaryCardProps) {
  return (
    <Card className="flex flex-col gap-6 p-8">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-heading-3 font-semibold text-fg">{summary.name}</h1>
          <p className="text-body-large text-fg-muted">{summary.description}</p>
        </div>
        <Button variant="secondary" size="sm">
          <PencilIcon className="size-4" />
          Edit
        </Button>
      </div>

      <dl className="flex flex-wrap gap-x-12 gap-y-4 border-t border-border-subtle pt-4">
        <MetaItem label="Project owner" value={summary.owner} />
        <MetaItem label="Start date" value={formatProjectDate(summary.startDate)} />
        <MetaItem label="End date" value={formatProjectDate(summary.endDate)} />
      </dl>
    </Card>
  );
}

function MetaItem({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-body-small text-fg-muted">{label}</dt>
      <dd className={value ? "text-body-large font-semibold text-fg" : "text-body-large text-fg-muted"}>
        {value ?? "Not set"}
      </dd>
    </div>
  );
}