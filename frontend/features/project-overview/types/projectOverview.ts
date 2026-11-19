export interface ProjectSummary {
  id: string;
  name: string;
  description: string;
  owner: string;
  startDate: string | null;
  endDate: string | null;
}

export interface Stakeholder {
  role: string;
  note: string;
}

export interface DiscoveryReadiness {
  percentComplete: number;
  reviewed: number;
  total: number;
  aiAssessed: number;
  criticalGaps: number;
  verified: number;
  missing: number;
  awaitingReview: number;
  nextGap: { topic: string; question: string } | null;
}

export interface ArtifactTemplate {
  id: string;
  name: string;
  description: string;
}

export interface ProjectOverview {
  summary: ProjectSummary;
  problemStatement: string;
  objectives: { items: string[]; isAiDraft: boolean };
  stakeholders: { internal: Stakeholder[]; external: Stakeholder[] };
  discovery: DiscoveryReadiness;
  artifacts: { draftCount: number; available: ArtifactTemplate[] };
}