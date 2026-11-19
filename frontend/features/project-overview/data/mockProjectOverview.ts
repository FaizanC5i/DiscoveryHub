import type { ProjectOverview } from "../types/projectOverview";

export const mockProjectOverview: ProjectOverview = {
  summary: {
    id: "unilever-consumer-insights-hub",
    name: "Unilever Consumer Insights Hub",
    description: "Lenovo data analysis",
    owner: "Anil N",
    startDate: null,
    endDate: null,
  },
  problemStatement:
    "Unilever Consumer Insights Hub is meant to replace a process that today is spread across disconnected tools and people. Ownership is unclear, information is duplicated or hard to find, and nobody has a reliable view of progress, which slows delivery and causes rework.",
  objectives: {
    isAiDraft: true,
    items: [
      "Define clear scope, ownership, and success measures for Unilever Consumer Insights Hub",
      "Bring the information and work behind Unilever Consumer Insights Hub into one shared place",
      "Give teams and stakeholders a clear view of status and next steps",
      "Reduce manual effort, duplication, and rework in the current process",
    ],
  },
  stakeholders: {
    internal: [
      { role: "Executive sponsor", note: "Suggested: approves scope and funding" },
      { role: "Project owner", note: "Suggested: accountable for delivery" },
      { role: "Delivery team", note: "Suggested: builds and operates the solution" },
      { role: "End users", note: "Suggested: use the solution day to day" },
    ],
    external: [
      { role: "Customers or requesters", note: "Suggested: depend on the outcome" },
    ],
  },
    discovery: {
    percentComplete: 13,
    reviewed: 2,
    total: 15,
    aiAssessed: 2,
    criticalGaps: 8,
    verified: 2,
    missing: 13,
    awaitingReview: 0,
    nextGap: {
      topic: "Stakeholder roles",
      question: "Which stakeholders sponsor, own, approve, or are affected by this project?",
    },
  },
  artifacts: {
    draftCount: 1,
    available: [
      { id: "brd", name: "BRD", description: "Business Requirements Document" },
      { id: "prd", name: "PRD", description: "Product Requirements Document" },
      {
        id: "solution-architecture",
        name: "Solution Architecture",
        description: "Components, integrations, data flows, and deployment",
      },
    ],
  },
};