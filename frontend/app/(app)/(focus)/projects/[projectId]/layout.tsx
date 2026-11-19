import type { ReactNode } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { getCurrentUser } from "@/features/auth/services/currentUser";
import { requireProjectForCurrentUser } from "@/features/projects/services/serverProjectService";

export const instant = false;

/**
 * Full-screen project pages (such as User Discovery).
 * Same header and access check as the (project) layout, but without the
 * Overview / Discovery Hub / Artifact Studio tabs and without the max-width box:
 * each page here draws its own bar and uses the whole width.
 */
export default async function FocusProjectLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const [user, project] = await Promise.all([getCurrentUser(), requireProjectForCurrentUser(projectId)]);

  return (
    <div className="flex min-h-dvh flex-col">
      <AppHeader user={user} title={project.name} width="full" />
      <div className="flex flex-1 flex-col">{children}</div>
    </div>
  );
}