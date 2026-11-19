import type { ReactNode } from "react";
import { EmptyState } from "@/components/feedback/EmptyState";
import type { Project } from "@/types/project";
import { ProjectCard } from "./ProjectCard";

interface RecentProjectsProps {
  projects: Project[];
  /** Shown in the empty state, for example a "Create your first project" button. */
  emptyAction?: ReactNode;
}

export function RecentProjects({ projects, emptyAction }: RecentProjectsProps) {
  return (
    <section aria-labelledby="recent-projects-heading" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 id="recent-projects-heading" className="text-title-small font-semibold text-fg">
          Recent projects
        </h2>
        <p className="text-body-small text-fg-muted">Continue where you left off</p>
      </div>

      {projects.length > 0 ? (
        <ul className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {projects.map((project) => (
            <li key={project.id}>
              <ProjectCard project={project} />
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          title="No projects yet"
          description="Create a project to start discovery from your documents."
          action={emptyAction}
        />
      )}
    </section>
  );
}
