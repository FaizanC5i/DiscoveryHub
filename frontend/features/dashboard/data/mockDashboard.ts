import { ROUTES } from "@/lib/constants";
import type { DashboardData } from "../types/dashboard";

/** Mock data for the dashboard until the projects API exists. */
export const MOCK_DASHBOARD: DashboardData = {
  projects: [
    {
      id: "unilever-consumer-insights-hub",
      name: "Unilever Consumer Insights Hub",
      description: "User Discovery assistant and artifact creation",
      status: "in_progress",
      discoveryCoverage: 0,
      updatedAt: "2026-11-05T17:49:00",
    },
    {
      id: "lenovo-4p",
      name: "Lenovo",
      description: "Lenovo 4P",
      status: "in_progress",
      discoveryCoverage: 0,
      updatedAt: "2026-11-05T17:48:00",
    },
  ],
  quickAccess: [
    {
      key: "exports",
      title: "Exports",
      description: "Download and review the artifacts you have generated.",
      href: ROUTES.exports,
    },
    {
      key: "mom-assistant",
      title: "MoM assistant",
      description: "Capture meeting minutes and turn them into next steps.",
      href: ROUTES.momAssistant,
    },
  ],
};
