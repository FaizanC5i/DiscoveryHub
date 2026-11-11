import type { BadgeTone } from "@/components/ui/Badge";
import type { ProjectStatus } from "./types/dashboard";

export const PROJECT_STATUS_DISPLAY: Record<ProjectStatus, { label: string; tone: BadgeTone }> = {
  in_progress: { label: "In progress", tone: "brand" },
  completed: { label: "Completed", tone: "success" },
  not_started: { label: "Not started", tone: "neutral" },
};
