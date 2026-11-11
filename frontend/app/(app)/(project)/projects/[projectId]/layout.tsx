import type { ReactNode } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { ContextLibraryPanel } from "@/features/context-library/components/ContextLibraryPanel";
import { ContextLibraryProvider } from "@/features/context-library/hooks/useContextLibrary";
import { getContextLibrary } from "@/features/context-library/services/contextLibraryService";
import { getCurrentUser } from "@/features/auth/services/currentUser";
import { getProjectOverview } from "@/features/project-overview/services/projectOverviewService";
import { ProjectSubNav } from "@/features/project-shell/components/ProjectSubNav";

export default async function ProjectLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const [user, overview, library] = await Promise.all([
    getCurrentUser(),
    getProjectOverview(projectId),
    getContextLibrary(projectId),
  ]);

  return (
    <div className="flex min-h-dvh flex-col">
      <AppHeader user={user} title={overview.summary.name} width="full" />
      <ContextLibraryProvider>
        <ProjectSubNav projectId={projectId} />
        <div className="flex flex-1">
          <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto w-full max-w-6xl">{children}</div>
          </main>
          <ContextLibraryPanel {...library} />
        </div>
      </ContextLibraryProvider>
    </div>
  );
}