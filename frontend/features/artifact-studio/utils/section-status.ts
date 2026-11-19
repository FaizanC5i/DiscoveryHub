import { badgeClass } from "@/features/discovery/utils/class-names";
import type { DraftSectionStatus } from "../types/artifact-studio.types";

/** Label and badge colour for each section status. */
export const SECTION_STATUS: Record<DraftSectionStatus, { label: string; badge: string }> = {
  NOT_STARTED: { label: "Not Started", badge: badgeClass.grey },
  DRAFT: { label: "Draft", badge: badgeClass.grey },
  PENDING_REVIEW: { label: "Ready for Review", badge: badgeClass.warning },
  NEEDS_CLARIFICATION: { label: "Needs Clarification", badge: badgeClass.error },
  APPROVED: { label: "Approved", badge: badgeClass.success },
};

/** 1 -> "01" */
export const sectionNumber = (n: number) => String(n).padStart(2, "0");