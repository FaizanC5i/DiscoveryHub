import { ROUTES } from "@/lib/constants";
import type { QuickAccessItem } from "../types/dashboard";

/** Shortcut cards on the dashboard. Static for now, so they live here rather than in the API. */
export const QUICK_ACCESS_ITEMS: QuickAccessItem[] = [
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
];
