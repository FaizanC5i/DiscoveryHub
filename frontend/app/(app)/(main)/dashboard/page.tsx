import type { Metadata } from "next";
import { Button } from "@/components/ui/Button";
import { PlusIcon } from "@/components/icons";
import { getCurrentUser } from "@/features/auth/services/currentUser";
import { DashboardHeading } from "@/features/dashboard/components/DashboardHeading";
import { QuickAccess } from "@/features/dashboard/components/QuickAccess";
import { RecentProjects } from "@/features/dashboard/components/RecentProjects";
import { getDashboardData } from "@/features/dashboard/services/dashboardService";

export const metadata: Metadata = {
  title: "Dashboard",
};

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
        action={
          <Button className="self-start sm:self-auto">
            <PlusIcon className="size-4" />
            Start new project
          </Button>
        }
      />
      <RecentProjects projects={projects} />
      <QuickAccess items={quickAccess} />
    </div>
  );
}
