import Link from "next/link";
import { ArrowRightIcon, FolderIcon } from "@/components/icons";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { ROUTES } from "@/lib/constants";
import { PROJECT_STATUS_DISPLAY } from "../constants";
import type { Project } from "../types/dashboard";
import { formatUpdatedAt } from "../utils/formatDate";

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const status = PROJECT_STATUS_DISPLAY[project.status];

  return (
    <Card className="flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <span className="flex size-10 items-center justify-center rounded-chip bg-surface-brand-subtle text-fg-brand">
          <FolderIcon className="size-5" />
        </span>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>

      <div className="flex flex-col gap-1">
        <h3 className="text-title-small font-semibold text-fg">{project.name}</h3>
        <p className="text-body-medium text-fg-muted">{project.description}</p>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-body-small text-fg-muted">
          <span>Discovery coverage</span>
          <span className="font-semibold text-fg">{project.discoveryCoverage}%</span>
        </div>
        <ProgressBar value={project.discoveryCoverage} label={`Discovery coverage for ${project.name}`} />
      </div>

      <div className="flex items-center justify-between gap-4 border-t border-border-subtle pt-4">
        <time dateTime={project.updatedAt} className="text-caption text-fg-muted">
          Updated {formatUpdatedAt(project.updatedAt)}
        </time>
        <Link
          href={ROUTES.project(project.id)}
          className="inline-flex items-center gap-1.5 text-body-medium font-semibold text-fg-brand hover:text-fg-brand-strong"
        >
          Open workspace
          <ArrowRightIcon className="size-4" />
        </Link>
      </div>
    </Card>
  );
}
