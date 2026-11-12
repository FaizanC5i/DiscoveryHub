import Link from "next/link";
import { ArrowRightIcon, FolderIcon } from "@/components/icons";
import { Card } from "@/components/ui/Card";
import { ROUTES } from "@/lib/constants";
import type { Project } from "@/types/project";
import { formatUpdatedAt } from "../utils/formatDate";

interface ProjectCardProps {
  project: Project;
}

/** One project in the recent list. Links to the project's overview page. */
export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Card className="flex flex-col gap-5 p-5 sm:p-6">
      <span className="flex size-10 items-center justify-center rounded-chip bg-surface-brand-subtle text-fg-brand">
        <FolderIcon className="size-5" />
      </span>

      <div className="flex flex-col gap-1">
        <h3 className="text-title-small font-semibold text-fg">{project.name}</h3>
        <p className="text-body-medium text-fg-muted">{project.description ?? "No description yet"}</p>
      </div>

      <div className="flex items-center justify-between gap-4 border-t border-border-subtle pt-4">
        <time dateTime={project.updated_at} className="text-caption text-fg-muted">
          Updated {formatUpdatedAt(project.updated_at)}
        </time>
        <Link
          href={ROUTES.projectDetail(project.id)}
          className="inline-flex items-center gap-1.5 text-body-medium font-semibold text-fg-brand hover:text-fg-brand-strong"
        >
          Open workspace
          <ArrowRightIcon className="size-4" />
        </Link>
      </div>
    </Card>
  );
}
