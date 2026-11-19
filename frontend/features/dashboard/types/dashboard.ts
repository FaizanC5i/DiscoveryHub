import type { Project } from "@/types/project";

export type QuickAccessKey = "exports" | "mom-assistant";

export interface QuickAccessItem {
  key: QuickAccessKey;
  title: string;
  description: string;
  href: string;
}

export interface DashboardData {
  /** The signed-in user's most recently updated projects, from the API. */
  projects: Project[];
  quickAccess: QuickAccessItem[];
}
