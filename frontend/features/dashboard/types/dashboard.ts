export type ProjectStatus = "in_progress" | "completed" | "not_started";

export interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  /** Percentage of discovery questions answered, from 0 to 100. */
  discoveryCoverage: number;
  /** ISO 8601 timestamp. */
  updatedAt: string;
}

export type QuickAccessKey = "exports" | "mom-assistant";

export interface QuickAccessItem {
  key: QuickAccessKey;
  title: string;
  description: string;
  href: string;
}

export interface DashboardData {
  projects: Project[];
  quickAccess: QuickAccessItem[];
}
