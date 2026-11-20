/**
 * PLACEHOLDER PRD backend, used until the backend can generate a PRD
 * (today it answers "PRD cannot be generated yet. Only the BRD is available.").
 *
 * It returns the same shapes as the real artifact endpoints and behaves like them:
 * Regenerate and Clarify mark the section as working for a few seconds (draft status
 * "Generating", which the editor polls), then the new text or the questions arrive.
 * Data lives in the browser tab and resets on a full page reload.
 *
 * Remove together with the PRD switch in artifact-studio.service.ts once the backend supports PRD.
 */
import { ApiError } from "@/lib/api/client";
import type {
  ArtifactDraft,
  ClarificationAnswer,
  DraftConfig,
  DraftSection,
  DraftSectionStatus,
  ExportOptions,
} from "../types/artifact-studio.types";

const RUN_MS = 3500; // how long a placeholder agent run takes

/** The 25 PRD sections agreed with the team. */
const PRD_SECTIONS: { id: string; title: string }[] = [
  { id: "document_overview", title: "Document Overview" },
  { id: "product_overview", title: "Product Overview & Background" },
  { id: "problem_objectives", title: "Problem Statement & Objectives" },
  { id: "target_users_personas", title: "Target Users & Personas" },
  { id: "product_scope", title: "Product Scope" },
  { id: "functional_requirements", title: "Functional Requirements" },
  { id: "user_stories_use_cases", title: "User Stories & Use Cases" },
  { id: "user_workflows", title: "User Workflows & Process Flows" },
  { id: "ui_ux_requirements", title: "UI/UX Requirements" },
  { id: "technical_architecture", title: "Technical Architecture & Design" },
  { id: "data_requirements", title: "Data Requirements" },
  { id: "api_integration", title: "API & Integration Requirements" },
  { id: "non_functional_requirements", title: "Non-Functional Requirements" },
  { id: "infrastructure_deployment", title: "Infrastructure & Deployment Requirements" },
  { id: "security_compliance", title: "Security & Compliance Requirements" },
  { id: "error_handling", title: "Error Handling & Edge Cases" },
  { id: "constraints_assumptions", title: "Constraints, Assumptions & Dependencies" },
  { id: "risks_mitigation", title: "Risks & Mitigation" },
  { id: "prioritization_mvp", title: "Prioritization & MVP Scope" },
  { id: "acceptance_criteria", title: "Acceptance Criteria" },
  { id: "testing_qa", title: "Testing & Quality Assurance" },
  { id: "success_metrics", title: "Success Metrics & KPIs" },
  { id: "timeline_release", title: "Timeline & Release Planning" },
  { id: "open_questions", title: "Open Questions & Pending Decisions" },
  { id: "appendices_references", title: "Appendices & References" },
];

/** Starting text for the sections the placeholder "already drafted". */
const STARTING_TEXT: Record<string, string[]> = {
  document_overview: [
    "Document: Product Requirements Document, version 0.1 (draft)",
    "Owner and approvers to be confirmed in Discovery",
    "Executive summary: one shared place for discovery evidence and generated requirements",
  ],
  product_overview: [
    "Consolidates discovery inputs that today sit across separate tools and people",
    "Builds on the approved discovery answers and the project context library",
  ],
  problem_objectives: [
    "Ownership is unclear and information is duplicated or hard to find",
    "Objective: give teams a reliable view of progress and next steps",
    "Objective: reduce manual effort, duplication, and rework",
  ],
  product_scope: [
    "In scope: discovery checklist, context library, artifact generation and export",
    "Out of scope: replacing downstream delivery and ticketing tools",
  ],
  functional_requirements: [
    "Users can upload sources and search the context library",
    "Users can review and approve discovery answers",
    "Users can generate, edit, and export requirement documents",
  ],
};

/** Sections that start with open questions instead of text (like "Needs Clarification" in the BRD). */
const STARTS_WITH_QUESTIONS = new Set(["target_users_personas"]);

/** First question for a section; the other two follow the same pattern as the real agent. */
const FIRST_QUESTION: Record<string, string> = {
  target_users_personas: "Which user groups need distinct product behavior, permissions, or workflows?",
  user_stories_use_cases: "Which user tasks matter most, and what does success look like for each?",
  technical_architecture: "Which existing systems must the product run alongside or replace?",
  data_requirements: "Which data sets does the product read or create, and who owns them?",
  non_functional_requirements: "What response times, availability, and user volumes must it support?",
  security_compliance: "Which privacy, residency, or regulatory rules apply to this product?",
  success_metrics: "Which numbers will show the product is working, and what are their targets?",
};

const questionsFor = (id: string, title: string): string[] => [
  FIRST_QUESTION[id] ?? `What must ${title} cover for this product?`,
  `What evidence, numbers, owners, or examples should ${title} reflect?`,
  "Is there anything that must not be assumed here?",
];

const missingReasonFor = (title: string) =>
  `${title} has no draft yet because no source material or context mentions it.`;

interface SectionState {
  id: string;
  number: number;
  title: string;
  status: DraftSectionStatus;
  bullets: string[];
  questions: string[];
  savedAnswers: ClarificationAnswer[];
}

interface Run {
  sectionId: string;
  kind: "regenerate" | "clarify";
  startedAt: number;
  answers: ClarificationAnswer[];
}

interface PrdState {
  title: string;
  sections: SectionState[];
  runs: Run[];
  version: number;
}

function initialState(): PrdState {
  return {
    title: "Product Requirements Document",
    version: 1,
    runs: [],
    sections: PRD_SECTIONS.map(({ id, title }, i) => {
      const bullets = STARTING_TEXT[id] ?? [];
      const asks = STARTS_WITH_QUESTIONS.has(id);
      return {
        id,
        number: i + 1,
        title,
        status: bullets.length ? "PENDING_REVIEW" : asks ? "NEEDS_CLARIFICATION" : "NOT_STARTED",
        bullets,
        questions: asks ? questionsFor(id, title) : [],
        savedAnswers: [],
      };
    }),
  };
}

let state: PrdState = initialState();

function sectionOrThrow(sectionId: string): SectionState {
  const section = state.sections.find((s) => s.id === sectionId);
  if (!section) throw new ApiError("This section does not exist.", 404, "SECTION_NOT_FOUND");
  return section;
}

/** Apply every placeholder run whose time is up. */
function settle() {
  const now = Date.now();
  const finished = state.runs.filter((run) => now - run.startedAt >= RUN_MS);
  state.runs = state.runs.filter((run) => now - run.startedAt < RUN_MS);

  for (const run of finished) {
    const section = state.sections.find((s) => s.id === run.sectionId);
    if (!section) continue;

    if (run.kind === "clarify") {
      section.questions = questionsFor(section.id, section.title);
      if (!section.bullets.length) section.status = "NEEDS_CLARIFICATION";
      continue;
    }

    // Regenerate: write from the answers (new and saved), or rephrase the current text.
    section.savedAnswers = [...section.savedAnswers, ...run.answers];
    const fromAnswers = section.savedAnswers.map((a) => a.answer);
    section.bullets = fromAnswers.length
      ? [...fromAnswers, `Drafted from your answers for ${section.title}`]
      : section.bullets.map((b) => b.replace(/ \(regenerated\)$/, "") + " (regenerated)");
    section.status = "PENDING_REVIEW";
    section.questions = [];
  }
}

function toDraftSection(section: SectionState): DraftSection {
  const isWorking = state.runs.some((run) => run.sectionId === section.id);
  const hasText = section.bullets.length > 0;
  return {
    id: section.id,
    number: section.number,
    title: section.title,
    status: section.status,
    bullets: section.bullets,
    content: section.bullets.map((b) => `- ${b}`).join("\n"),
    missingReason: hasText ? undefined : missingReasonFor(section.title),
    clarificationQuestions: section.questions.length ? section.questions : undefined,
    isWorking,
    lastError: null,
  };
}

function startRun(sectionId: string, kind: Run["kind"], answers: ClarificationAnswer[] = []) {
  settle();
  if (state.runs.some((run) => run.sectionId === sectionId)) {
    throw new ApiError("The agent is already working on this section.", 409, "RUN_IN_PROGRESS");
  }
  state.runs = [...state.runs, { sectionId, kind, startedAt: Date.now(), answers }];
}

/* ---- The same operations as the real endpoints ---------------------------------------------- */

export async function generatePrd(config: DraftConfig): Promise<void> {
  state = initialState();
  if (config.title.trim()) state.title = config.title.trim();
}

export async function getPrdDraft(): Promise<ArtifactDraft> {
  settle();
  const drafted = state.sections.filter((s) => s.bullets.length > 0).length;
  return {
    artifactCode: "PRD",
    artifactName: "Product Requirements Document",
    title: state.title,
    description: `${drafted} of ${state.sections.length} sections drafted`,
    status: state.runs.length ? "Generating" : "In Progress",
    isClientReady: false,
    snapshot: { verified: 2, total: 15, sources: 1, missing: 13, unreviewedExcluded: 0 },
    versions: [{ number: state.version, label: "Just now", isCurrent: true }],
    sections: state.sections.map(toDraftSection),
    isOutdated: false,
    newAnswerCount: 0,
  };
}

export async function savePrdSectionContent(sectionId: string, content: string): Promise<DraftSection> {
  settle();
  const section = sectionOrThrow(sectionId);
  section.bullets = content
    .split("\n")
    .map((line) => line.replace(/^\s*[-*]\s+/, "").trim())
    .filter(Boolean);
  section.status = section.bullets.length ? "APPROVED" : "NOT_STARTED";
  section.questions = [];
  return toDraftSection(section);
}

export async function regeneratePrdSection(sectionId: string, answers: ClarificationAnswer[]): Promise<void> {
  const section = sectionOrThrow(sectionId);
  if (!answers.length && !section.bullets.length && !section.savedAnswers.length) {
    // Same rule as the real backend: nothing to write from yet.
    throw new ApiError(
      `${section.title} has nothing to write from yet. Use Clarify first.`,
      409,
      "NOTHING_TO_WRITE_FROM",
    );
  }
  startRun(sectionId, "regenerate", answers);
}

export async function clarifyPrdSection(sectionId: string): Promise<void> {
  sectionOrThrow(sectionId);
  startRun(sectionId, "clarify");
}

export async function refreshPrd(): Promise<void> {
  settle();
  for (const section of state.sections) {
    if (section.bullets.length && !state.runs.some((run) => run.sectionId === section.id)) {
      state.runs.push({ sectionId: section.id, kind: "regenerate", startedAt: Date.now(), answers: [] });
    }
  }
}

export async function savePrdVersion(): Promise<number> {
  state.version += 1;
  return state.version;
}

export async function exportPrd(options: ExportOptions): Promise<{ fileName: string; blob: Blob }> {
  if (options.format !== "md") {
    throw new ApiError("Word and PDF export for the PRD will work once the backend supports the PRD. Choose Markdown for now.", 400, "EXPORT_NOT_AVAILABLE");
  }
  settle();
  const lines = [`# ${state.title}`, "", "> Incomplete draft: discovery is not complete. Not client-ready.", ""];
  for (const section of state.sections) {
    lines.push(`## ${String(section.number).padStart(2, "0")} ${section.title}`, "");
    if (section.bullets.length) section.bullets.forEach((b) => lines.push(`- ${b}`));
    else lines.push(`_${missingReasonFor(section.title)}_`);
    if (options.includeOpenQuestions && section.questions.length) {
      lines.push("", "**Open questions**", "");
      section.questions.forEach((q) => lines.push(`- ${q}`));
    }
    lines.push("");
  }
  return { fileName: "prd-draft.md", blob: new Blob([lines.join("\n")], { type: "text/markdown" }) };
}