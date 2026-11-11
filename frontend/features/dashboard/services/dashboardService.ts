import { MOCK_DASHBOARD } from "../data/mockDashboard";
import type { DashboardData } from "../types/dashboard";

/**
 * Dashboard data boundary. Components receive data from here, not from mock files.
 * Replace the body with `apiRequest<DashboardData>("/dashboard")` when the backend exists.
 */
export async function getDashboardData(): Promise<DashboardData> {
  return MOCK_DASHBOARD;
}
