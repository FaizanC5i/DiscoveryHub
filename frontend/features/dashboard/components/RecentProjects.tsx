import { EmptyState } from "@/components/feedback/EmptyState";
import type { Project } from "../types/dashboard";
import { ProjectCard } from "./ProjectCard";

interface RecentProjectsProps {
  projects: Project[];
}

export function RecentProjects({ projects }: RecentProjectsProps) {
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
          description="Start a new project to begin discovery from your documents."
        />
      )}
    </section>
  );
}
