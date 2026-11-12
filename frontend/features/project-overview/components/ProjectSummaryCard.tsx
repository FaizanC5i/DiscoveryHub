import { Card } from "@/components/ui/Card";
import { EditProjectButton } from "@/features/projects/components/EditProjectButton";
import type { Project } from "@/types/project";
import { formatProjectDate, formatProjectTimestamp } from "../utils/formatProjectDate";

interface ProjectSummaryCardProps {
  project: Project;
}

/**
 * Header card for the overview: the project's name, description, and every detail
 * the user entered. Empty optional fields show "Not set", so a blank is never mistaken for missing data.
 */
export function ProjectSummaryCard({ project }: ProjectSummaryCardProps) {
  return (
    <Card className="flex flex-col gap-6 p-8">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-heading-3 font-semibold text-fg">{project.name}</h1>
          <p className={project.description ? "text-body-large text-fg-muted" : "text-body-large text-fg-disabled"}>
            {project.description ?? "Not set"}
          </p>
        </div>
        <EditProjectButton project={project} />
      </div>

      <dl className="flex flex-wrap gap-x-12 gap-y-4 border-t border-border-subtle pt-4">
        <MetaItem label="Project owner" value={project.owner_name} />
        <MetaItem label="Start date" value={formatProjectDate(project.start_date)} />
        <MetaItem label="End date" value={formatProjectDate(project.end_date)} />
        <MetaItem label="Created" value={formatProjectTimestamp(project.created_at)} />
        <MetaItem label="Last updated" value={formatProjectTimestamp(project.updated_at)} />
      </dl>
    </Card>
  );
}

function MetaItem({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-body-small text-fg-muted">{label}</dt>
      <dd className={value ? "text-body-large font-semibold text-fg" : "text-body-large text-fg-disabled"}>
        {value ?? "Not set"}
      </dd>
    </div>
  );
}
