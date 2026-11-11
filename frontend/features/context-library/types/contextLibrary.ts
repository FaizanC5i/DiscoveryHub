export type PillarId = "user" | "data" | "tech";
export type SourceOrigin = "uploaded" | "auto-synthesized";

export interface PillarProgress {
  id: PillarId;
  reviewed: number;
  total: number;
}

export interface DiscoveryProgress {
  percentComplete: number;
  reviewed: number;
  total: number;
  unresolved: number;
  awaitingReview: number;
  pillars: PillarProgress[];
}

export interface ContextSource {
  id: string;
  name: string;
  pillar: PillarId;
  origin: SourceOrigin;
}

export interface ContextLibrary {
  progress: DiscoveryProgress;
  sources: ContextSource[];
}