export interface EvidenceItem {
  chunk_id: number;
  source_title: string;
  page_number: number | null;
  chunk_text: string;
  reason?: string;
}

export interface ProposalView {
  id: number;
  proposed_answer: string;
  agent_status: string;
  is_completed: boolean;
  completion_score: number | null;
  base_version_number: number;
  created_at: string | null;
  missing_information: string[];
  clarification_questions: string[];
  evidence: EvidenceItem[];
}

export interface CurrentAnswer {
  text: string;
  status: string;
  is_completed: boolean;
  completion_score: number | null;
  approved_at: string | null;
}

export interface CheckpointCard {
  checkpoint: { id: number; code: string; name: string; question: string };
  current_answer: CurrentAnswer | null;
  chunk_count: number;
  evidence: EvidenceItem[];
  pending_proposal: ProposalView | null;
}

export interface UserDiscoveryOverview {
  running: boolean;
  pending_mapping_chunks: number;
  failed_mapping_chunks: number;
  checkpoints: CheckpointCard[];
}

export interface ApprovalResult {
  proposal_id: number;
  checkpoint_answer_id: number;
  version_number: number;
}