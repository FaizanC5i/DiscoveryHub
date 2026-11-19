export type PillarId = "USER" | "DATA" | "TECH";
export type GapPriority = "critical" | "recommended";
export type GapStatus = "no-evidence" | "awaiting-review";

export interface Gap {
  id: string;
  question: string;
  whyItMatters: string;
  source: string; // checkpoint name shown in the "Source" chip
  priority: GapPriority;
  status: GapStatus;
}

export interface Pillar {
  id: PillarId;
  name: string;
  shortName: string;
  description: string;
  verified: number; // checkpoints approved by a person
  total: number;
  gaps: Gap[];
}

export type SourceStatus = "Uploaded" | "Auto-synthesized" | "Processing";

export interface Source {
  id: string;
  title: string;
  status: SourceStatus;
  pillars: PillarId[];
  createdBy: string;
}

export interface DiscoveryStats {
  verified: number;
  total: number;
  percent: number;
  unresolved: number;
  criticalGaps: number;
  noEvidence: number;
  awaitingReview: number;
}

export interface ProjectSummary {
  id: string;
  name: string;
}

export interface CurrentUser {
  name: string;
}

/** Everything the Discovery Hub page needs, loaded in one call. */
export interface DiscoveryOverview {
  project: ProjectSummary;
  user: CurrentUser;
  targetPercent: number;
  pillars: Pillar[];
  sources: Source[];
}