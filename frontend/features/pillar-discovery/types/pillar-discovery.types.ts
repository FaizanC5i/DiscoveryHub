import type { PillarId } from "@/features/discovery/types/discovery.types";

/** The five design-thinking phases shown under "Guided design thinking". */
export type PhaseId = "EMPATHIZE" | "DEFINE" | "IDEATE" | "PROTOTYPE" | "TEST";

export type QuestionStatus = "open" | "answered";
export type QuestionPriority = "critical" | "recommended";

/** One checklist item (a discovery checkpoint) inside a pillar. */
export interface ChecklistQuestion {
  id: string; // "Q01"
  status: QuestionStatus;
  priority: QuestionPriority;
  /** Phase whose activities help answer this question; shown on the card and in "Get help". */
  phaseId: PhaseId;
  question: string;
  /** What evidence is still missing. Only for open questions. */
  missing?: string;
  /** The approved answer. Only for answered questions. */
  answer?: string;
  /** Artifacts that need this answer, shown as "Source" chips (BRD, PRD, ...). */
  sources: string[];
}

export type PhaseArtifactStatus = "uploaded" | "awaiting-review" | "draft" | "not-started";

export interface PhaseArtifactFile {
  name: string;
  meta: string; // "3 personas · uploaded Nov 5"
}

/** One evidence artifact inside a phase (User personas, Empathy map, ...). */
export interface PhaseArtifact {
  id: string;
  title: string;
  description: string;
  /** Question ids this artifact helps answer. */
  informs: string[];
  status: PhaseArtifactStatus;
  file?: PhaseArtifactFile;
}

export interface DesignPhase {
  id: PhaseId;
  number: number; // 1 -> "01"
  name: string; // "Empathize"
  tagline: string; // "Understand the people behind the project."
  description: string;
  /** Question ids this phase helps answer. */
  questionIds: string[];
  artifacts: PhaseArtifact[];
}

export type RelevantSourceStatus = "Uploaded" | "Awaiting review" | "Auto-synthesized" | "Processing";

/** A context-library source linked to this pillar. */
export interface RelevantSource {
  id: string;
  title: string;
  pillars: PillarId[];
  phaseName?: string; // "Empathize"
  status: RelevantSourceStatus;
  createdBy: string;
}

/** Everything the pillar discovery page needs for one pillar, loaded in one call. */
export interface PillarDiscovery {
  pillarId: PillarId;
  name: string; // "User Discovery"
  description: string;
  targetPercent: number;
  questions: ChecklistQuestion[];
  phases: DesignPhase[];
  relevantSources: RelevantSource[];
}

/** Numbers shown in the checklist badges, worked out from the questions. */
export interface PillarProgress {
  answered: number;
  total: number;
  percent: number;
  open: number;
  criticalGaps: number;
}