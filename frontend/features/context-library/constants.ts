import type { BadgeTone } from "@/components/ui/Badge";
import type { PillarId, SourceOrigin } from "./types/contextLibrary";

export const PILLAR_LABELS: Record<PillarId, string> = {
  user: "User",
  data: "Data",
  tech: "Tech",
};

export const SOURCE_ORIGINS: Record<SourceOrigin, { label: string; tone: BadgeTone }> = {
  uploaded: { label: "Uploaded", tone: "neutral" },
  "auto-synthesized": { label: "Auto-synthesized", tone: "brand" },
};