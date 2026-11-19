import type { PillarId } from "@/features/discovery/types/discovery.types";

export type ArtifactCode =
  | "BRD"
  | "PRD"
  | "PROBLEM_STATEMENT"
  | "USER_PERSONAS"
  | "USER_STORIES"
  | "DATA_DICTIONARY"
  | "ONTOLOGY"
  | "SOLUTION_ARCHITECTURE"
  | "NFR";

export interface ArtifactType {
  code: ArtifactCode;
  name: string; // "BRD"
  description: string; // "Business Requirements Document"
}

/** An artifact already generated for this project. */
export interface AvailableArtifact {
  code: ArtifactCode;
  status: "ready" | "draft";
}

export type PillarReadinessStatus = "Not started" | "In progress" | "Complete";

export interface PillarReadiness {
  pillarId: PillarId;
  label: string; // "User"
  status: PillarReadinessStatus;
  verified: number;
  total: number;
  missing: number;
  review: number; // awaiting review
}

/** Evidence readiness for one artifact type. */
export interface ArtifactReadiness {
  percent: number;
  verified: number;
  awaitingReview: number;
  withoutEvidence: number;
  total: number;
  pillars: PillarReadiness[];
}

/** Everything the Artifact Studio page needs (besides the shared discovery data). */
export interface ArtifactStudioData {
  artifactTypes: ArtifactType[];
  availableArtifacts: AvailableArtifact[];
  audiences: string[];
  /** Readiness for each artifact type, keyed by its code. */
  readiness: Record<ArtifactCode, ArtifactReadiness>;
}

/* ---- Draft generation ---------------------------------------------------- */

export interface DraftConfig {
  title: string;
  audience: string;
  scope: string;
}

/* ---- Draft editor (the generated document) ------------------------------- */

/** Matches project_artifact_sections.status in the DB design. */
export type DraftSectionStatus = "NOT_STARTED" | "DRAFT" | "PENDING_REVIEW" | "NEEDS_CLARIFICATION" | "APPROVED";

export interface DraftSection {
  id: string;
  number: number; // 1 -> shown as "01"
  title: string;
  status: DraftSectionStatus;
  bullets: string[];
  /** The section text as Markdown (lists, tables). `bullets` is the same text as plain points. */
  content?: string;
  /** Why the agent could not write the section (empty when it has text). */
  missingReason?: string;
  /** The agent's open questions. Answering them rewrites the section. */
  clarificationQuestions?: string[];
  /** The draft waiting for review, when there is one. */
  proposalId?: number;
  /** The agent is working on this section right now. */
  isWorking?: boolean;
  /** Why the last agent run for this section failed. */
  lastError?: string | null;
}

/** One answer to an agent question, sent with Regenerate. */
export interface ClarificationAnswer {
  question: string;
  answer: string;
}

export interface DraftVersion {
  number: number;
  label: string; // "Just now", "Nov 5, 5:49 PM"
  isCurrent: boolean;
}

export interface DraftSnapshot {
  verified: number;
  total: number;
  sources: number;
  missing: number;
  unreviewedExcluded: number;
}

export interface ArtifactDraft {
  artifactCode: ArtifactCode;
  artifactName: string; // "Business Requirements Document"
  title: string;
  description: string;
  status: string; // "In Progress"
  isClientReady: boolean;
  snapshot: DraftSnapshot;
  versions: DraftVersion[];
  sections: DraftSection[];
  /** An answer was approved after this draft was generated: Refresh would use it. */
  isOutdated?: boolean;
  /** How many answers were approved since this draft was generated. */
  newAnswerCount?: number;
}

export type ExportFormat = "md" | "docx" | "pdf";

export interface ExportOptions {
  format: ExportFormat;
  includeSourceReferences: boolean;
  includeOpenQuestions: boolean;
}