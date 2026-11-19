import type { Metadata } from "next";
import { CreateProjectButton } from "@/features/projects/components/CreateProjectButton";
import { getCurrentUser } from "@/features/auth/services/currentUser";
import { DashboardHeading } from "@/features/dashboard/components/DashboardHeading";
import { QuickAccess } from "@/features/dashboard/components/QuickAccess";
import { RecentProjects } from "@/features/dashboard/components/RecentProjects";
import { getDashboardData } from "@/features/dashboard/services/dashboardService";

export const metadata: Metadata = {
  title: "Dashboard",
};

export const instant = false;

export default async function DashboardPage() {
  const [user, { projects, quickAccess }] = await Promise.all([
    getCurrentUser(),
    getDashboardData(),
  ]);

  const firstName = user.name.split(" ")[0];

  return (
    <div className="flex flex-col gap-10">
      <DashboardHeading
        firstName={firstName}
        action={<CreateProjectButton className="self-start sm:self-auto" />}
      />
      <RecentProjects
        projects={projects}
        emptyAction={<CreateProjectButton label="Create your first project" />}
      />
      <QuickAccess items={quickAccess} />
    </div>
  );
}
