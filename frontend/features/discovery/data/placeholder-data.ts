/**
 * PLACEHOLDER DATA for the Discovery Hub page (matches the PDF).
 * Replace with API data when the backend is ready.
 */
import type { Pillar, Source } from "../types/discovery.types";

export const placeholderUser = { name: "Alex Kim" };

export const placeholderProject = { name: "Unilever Consumer Insights Hub" };

export const TARGET_PERCENT = 80;

export const placeholderPillars: Pillar[] = [
  {
    id: "USER",
    name: "User Discovery",
    shortName: "User",
    description: "People, roles, stakeholders, process and workflow detail",
    verified: 1,
    total: 5,
    gaps: [
      { id: "USER-02", question: "Which stakeholders sponsor, own, approve, or are affected by this project?", whyItMatters: "Approvals and ownership depend on knowing who is accountable.", source: "Stakeholder roles", priority: "critical", status: "no-evidence" },
      { id: "USER-03", question: "How is this work done today, step by step, including handoffs?", whyItMatters: "The current process shows what the solution must change.", source: "Workflows and processes", priority: "critical", status: "no-evidence" },
      { id: "USER-04", question: "What are the biggest pain points users face today?", whyItMatters: "Pain points anchor the problem statement and success measures.", source: "Pain points", priority: "critical", status: "no-evidence" },
      { id: "USER-05", question: "What must the solution do for each user group?", whyItMatters: "Requirements turn discovery into scope.", source: "User requirements", priority: "recommended", status: "no-evidence" },
    ],
  },
  {
    id: "DATA",
    name: "Data Discovery",
    shortName: "Data",
    description: "Data sources, quality, ownership, data flows and governance",
    verified: 1,
    total: 5,
    gaps: [
      { id: "DATA-02", question: "Who owns and governs each data set?", whyItMatters: "Access decisions and accountability need a named owner.", source: "Data ownership", priority: "critical", status: "no-evidence" },
      { id: "DATA-03", question: "Which privacy, retention, or residency rules apply to this data?", whyItMatters: "Compliance obligations constrain design and scope.", source: "Privacy and retention", priority: "critical", status: "no-evidence" },
      { id: "DATA-04", question: "How reliable and complete is that data today?", whyItMatters: "Poor data quality changes scope and risk.", source: "Data quality", priority: "recommended", status: "no-evidence" },
      { id: "DATA-05", question: "How does data move between systems?", whyItMatters: "Data flows shape integration and timing.", source: "Data flows", priority: "recommended", status: "no-evidence" },
    ],
  },
  {
    id: "TECH",
    name: "Tech Discovery",
    shortName: "Tech",
    description: "Systems, architecture, integrations and security",
    verified: 0,
    total: 5,
    gaps: [
      { id: "TECH-01", question: "Which existing systems does the solution replace or sit alongside?", whyItMatters: "Migration and coexistence shape the plan.", source: "Existing systems", priority: "critical", status: "no-evidence" },
      { id: "TECH-02", question: "Which systems must it integrate with, and how?", whyItMatters: "Integrations drive effort, dependencies, and risk.", source: "Integrations", priority: "critical", status: "no-evidence" },
      { id: "TECH-03", question: "What security and access-control requirements apply?", whyItMatters: "Security requirements are non-negotiable inputs to the PRD.", source: "Security", priority: "critical", status: "no-evidence" },
      { id: "TECH-04", question: "What technical constraints or standards must the solution follow?", whyItMatters: "Constraints rule out options early.", source: "Technical constraints", priority: "recommended", status: "no-evidence" },
      { id: "TECH-05", question: "Where will the solution be hosted and operated?", whyItMatters: "Hosting affects cost, security, and delivery.", source: "Infrastructure", priority: "recommended", status: "no-evidence" },
    ],
  },
];

export const placeholderSources: Source[] = [
  { id: "501", title: "Flow_Implementation_Spec_Template.docx", status: "Uploaded", pillars: ["USER", "DATA"], createdBy: "Alex Kim" },
  { id: "502", title: "Project brief (auto-synthesized).md", status: "Auto-synthesized", pillars: ["USER", "DATA", "TECH"], createdBy: "Discovery Hub" },
];