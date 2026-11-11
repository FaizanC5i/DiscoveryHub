import type { ContextLibrary } from "../types/contextLibrary";

export const mockContextLibrary: ContextLibrary = {
  progress: {
    percentComplete: 13,
    reviewed: 2,
    total: 15,
    unresolved: 13,
    awaitingReview: 0,
    pillars: [
      { id: "user", reviewed: 1, total: 5 },
      { id: "data", reviewed: 1, total: 5 },
      { id: "tech", reviewed: 0, total: 5 },
    ],
  },
  sources: [
    { id: "src-1", name: "Flow_Implementation_Spec_Template.docx", pillar: "tech", origin: "uploaded" },
    { id: "src-2", name: "Project brief (auto-synthesized).md", pillar: "user", origin: "auto-synthesized" },
  ],
};