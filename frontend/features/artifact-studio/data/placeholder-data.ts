/**
 * PLACEHOLDER DATA for the Artifact Studio page (matches the PDF).
 * Replace with API data when the backend is ready.
 */
import type { ArtifactDraft, ArtifactReadiness, ArtifactType, AvailableArtifact } from "../types/artifact-studio.types";

export const artifactTypes: ArtifactType[] = [
  { code: "BRD", name: "BRD", description: "Business Requirements Document" },
  { code: "PRD", name: "PRD", description: "Product Requirements Document" },
  { code: "PROBLEM_STATEMENT", name: "Problem Statement", description: "A structured statement of the problem" },
  { code: "USER_PERSONAS", name: "User Personas", description: "Representative users and their context" },
  { code: "USER_STORIES", name: "User Stories", description: "Stories with acceptance criteria" },
  { code: "DATA_DICTIONARY", name: "Data Dictionary", description: "Entities, fields, owners, and quality rules" },
  { code: "ONTOLOGY", name: "Ontology", description: "Concepts, relationships, and shared vocabulary" },
  { code: "SOLUTION_ARCHITECTURE", name: "Solution Architecture", description: "Components, integrations, data flows, and deployment" },
  { code: "NFR", name: "NFR", description: "Non-functional requirements and targets" },
];

export const availableArtifacts: AvailableArtifact[] = [
  { code: "BRD", status: "ready" },
  { code: "PRD", status: "draft" },
  { code: "SOLUTION_ARCHITECTURE", status: "ready" },
];

export const audiences = ["Executive sponsor", "Project owner", "Delivery team", "End users"];

/** PLACEHOLDER: the PDF shows the same readiness for every artifact type. */
export const placeholderReadiness: ArtifactReadiness = {
  percent: 0,
  verified: 0,
  awaitingReview: 0,
  withoutEvidence: 15,
  total: 15,
  pillars: [
    { pillarId: "USER", label: "User", status: "Not started", verified: 0, total: 5, missing: 5, review: 0 },
    { pillarId: "DATA", label: "Data", status: "Not started", verified: 0, total: 5, missing: 5, review: 0 },
    { pillarId: "TECH", label: "Tech", status: "Not started", verified: 0, total: 5, missing: 5, review: 0 },
  ],
};

/* ---- Draft editor placeholder (matches the last page of the PDF) ---------- */

const PROJECT = "Unilever Consumer Insights Hub";

export const placeholderDraft: ArtifactDraft = {
  artifactCode: "BRD",
  artifactName: "Business Requirements Document",
  title: PROJECT,
  description: "User Discovery assistant and artifact creation",
  status: "In Progress",
  isClientReady: false,
  snapshot: { verified: 2, total: 15, sources: 1, missing: 13, unreviewedExcluded: 0 },
  versions: [{ number: 1, label: "Just now", isCurrent: true }],
  sections: [
    {
      id: "s1",
      number: 1,
      title: "Business Objectives",
      status: "PENDING_REVIEW",
      bullets: [
        `Define clear scope, ownership, and success measures for ${PROJECT}`,
        `Bring the information and work behind ${PROJECT} into one shared place`,
        "Give teams and stakeholders a clear view of status and next steps",
        "Reduce manual effort, duplication, and rework in the current process",
      ],
    },
    {
      id: "s2",
      number: 2,
      title: "Users & Stakeholders",
      status: "NEEDS_CLARIFICATION",
      bullets: [],
      missingReason: "No approved answer yet for stakeholder roles or personas.",
      clarificationQuestions: [
        "Who sponsors this project and approves its scope and funding?",
        "Which user groups will use the solution day to day?",
      ],
    },
    {
      id: "s3",
      number: 3,
      title: "Current State",
      status: "PENDING_REVIEW",
      bullets: [
        "Work is spread across disconnected tools and people",
        "Information is duplicated or hard to find",
        "Nobody has a reliable view of progress",
      ],
    },
    {
      id: "s4",
      number: 4,
      title: "Scope",
      status: "PENDING_REVIEW",
      bullets: [
        "In scope: consolidating discovery inputs into one shared workspace",
        "Out of scope: replacing downstream delivery tools",
      ],
    },
    {
      id: "s5",
      number: 5,
      title: "Functional Requirements",
      status: "PENDING_REVIEW",
      bullets: [
        "Users can upload and search project sources",
        "Users can review and approve discovery answers",
        "Users can generate and export requirement drafts",
      ],
    },
  ],
};