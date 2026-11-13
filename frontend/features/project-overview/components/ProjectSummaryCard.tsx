import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DeleteProjectButton } from "@/features/projects/components/DeleteProjectButton";
import { EditProjectButton } from "@/features/projects/components/EditProjectButton";
import type { Project } from "@/types/project";
import { formatProjectDate } from "../utils/formatProjectDate";

interface ProjectSummaryCardProps {
  project: Project;
}

/** Header of the overview: name, description, owner and dates, matching the design. */
export function ProjectSummaryCard({ project }: ProjectSummaryCardProps) {
  return (
    <Card className="flex flex-col gap-6 p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex min-w-0 flex-col gap-1">
          <h1 className="text-heading-4 font-semibold text-fg">{project.name}</h1>
          <p
            className={
              project.description
                ? "line-clamp-3 whitespace-pre-line text-body-large text-fg-muted"
                : "text-body-large text-fg-disabled"
            }
          >
            {project.description ?? "Not set"}
          </p>
        </div>

        <div className="flex shrink-0 gap-3">
          <Button variant="outline" disabled title="Yet to be done">
            Previous Artifacts
          </Button>
          <EditProjectButton project={project} />
          <DeleteProjectButton project={project} />
        </div>
      </div>

      <dl className="flex flex-wrap gap-x-12 gap-y-4 border-t border-border-subtle pt-4">
        <FieldValue label="Project owner" value={project.owner_name} />
        <FieldValue label="Start date" value={formatProjectDate(project.start_date)} />
        <FieldValue label="End date" value={formatProjectDate(project.end_date)} />
      </dl>
    </Card>
  );
}

function FieldValue({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-body-small text-fg-muted">{label}</dt>
      <dd
        className={
          value ? "text-body-medium font-semibold text-fg" : "text-body-medium text-fg-disabled"
        }
      >
        {value ?? "Not set"}
      </dd>
    </div>
  );
}