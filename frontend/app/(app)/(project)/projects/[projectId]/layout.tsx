import type { ReactNode } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { getCurrentUser } from "@/features/auth/services/currentUser";
import { requireProjectForCurrentUser } from "@/features/projects/services/serverProjectService";
import { ProjectSubNav } from "@/features/project-shell/components/ProjectSubNav";

export const instant = false;

export default async function ProjectLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const [user, project] = await Promise.all([
    getCurrentUser(),
    requireProjectForCurrentUser(projectId),
  ]);

  return (
    <div className="flex min-h-dvh flex-col">
      <AppHeader user={user} title={project.name} width="full" />
      <ProjectSubNav projectId={projectId} />
      <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto w-full max-w-6xl">{children}</div>
      </main>
    </div>
  );
}
