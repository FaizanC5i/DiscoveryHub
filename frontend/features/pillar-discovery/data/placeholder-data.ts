/**
 * PLACEHOLDER DATA for the User Discovery page (matches the design).
 * Phases 02–05 are collapsed in the design, so their artifacts are sensible
 * placeholders until the product team confirms them.
 * Replace with API data when the backend is ready.
 */
import type { DesignPhase, PhaseArtifact, PhaseId, PillarDiscovery } from "../types/pillar-discovery.types";

const placeholderUserDiscoveryBase: PillarDiscovery = {
  pillarId: "USER",
  name: "User Discovery",
  description:
    "People, roles, stakeholders, process and workflow detail. Answer an open question directly, or use a guided design-thinking activity to create the evidence you need.",
  targetPercent: 80,

  questions: [
    {
      id: "Q01",
      status: "open",
      priority: "critical",
      phaseId: "EMPATHIZE",
      question: "Which stakeholders sponsor, own, approve, or are affected by this project?",
      missing: "Stakeholder roles and decision ownership.",
      sources: ["BRD"],
    },
    {
      id: "Q02",
      status: "open",
      priority: "critical",
      phaseId: "DEFINE",
      question: "How is this work done today, step by step, including handoffs?",
      missing: "The current workflow and exception handoffs.",
      sources: ["BRD", "PRD"],
    },
    {
      id: "Q03",
      status: "open",
      priority: "critical",
      phaseId: "DEFINE",
      question: "What are the biggest pain points users face today?",
      missing: "Evidence of user frustrations and their impact.",
      sources: ["BRD"],
    },
    {
      id: "Q04",
      status: "open",
      priority: "recommended",
      phaseId: "IDEATE",
      question: "What must the solution do for each user group?",
      missing: "Prioritised needs for each user group.",
      sources: ["PRD"],
    },
    {
      id: "Q05",
      status: "answered",
      priority: "critical",
      phaseId: "EMPATHIZE",
      question: "Who uses the system, and what are their roles?",
      answer: "Three user groups, with goals, daily volumes and frustrations, from the uploaded personas.",
      sources: ["BRD", "PRD"],
    },
  ],

  phases: [
    {
      id: "EMPATHIZE",
      number: 1,
      name: "Empathize",
      tagline: "Understand the people behind the project.",
      description:
        "Identify sponsors, owners and affected users. Interview representatives, and capture their goals, frustrations and decision rights.",
      questionIds: ["Q01", "Q05"],
      artifacts: [
        {
          id: "user-personas",
          title: "User personas",
          description: "Represent the main user groups, their goals, daily volumes and frustrations.",
          informs: ["Q05", "Q01"],
          status: "uploaded",
          file: { name: "NorthStar_User_Personas_v1.pdf", meta: "3 personas · uploaded Nov 5" },
        },
        {
          id: "empathy-map",
          title: "Empathy map",
          description: "Capture what each user group thinks, feels, says and does.",
          informs: ["Q01", "Q03"],
          status: "not-started",
        },
        {
          id: "stakeholder-interview-notes",
          title: "Stakeholder interview notes",
          description: "Record who sponsors, owns and approves the work, from interviews or transcripts.",
          informs: ["Q01"],
          status: "not-started",
        },
      ],
    },
    {
      id: "DEFINE",
      number: 2,
      name: "Define",
      tagline: "Make the workflow and core problem explicit.",
      description:
        "Map today's workflow step by step, including handoffs, and turn the pain points into a clear problem statement.",
      questionIds: ["Q02", "Q03"],
      artifacts: [
        {
          id: "current-process-map",
          title: "Current-state process map",
          description: "Show each step of today's workflow, who does it, and where work is handed off.",
          informs: ["Q02"],
          status: "awaiting-review",
          file: { name: "Current process.pdf", meta: "uploaded Nov 5 · awaiting review" },
        },
        {
          id: "pain-point-log",
          title: "Pain point log",
          description: "List user frustrations with how often they happen and their impact.",
          informs: ["Q03"],
          status: "not-started",
        },
        {
          id: "problem-statement",
          title: "Problem statement",
          description: "Summarise the core problem in a few sentences everyone can agree on.",
          informs: ["Q02", "Q03"],
          status: "not-started",
        },
      ],
    },
    {
      id: "IDEATE",
      number: 3,
      name: "Ideate",
      tagline: "Explore solutions before choosing capabilities.",
      description: "Generate options for each pain point, then shortlist the capabilities worth testing.",
      questionIds: ["Q04"],
      artifacts: [
        {
          id: "how-might-we",
          title: "How-might-we list",
          description: "Reframe each pain point as an opportunity to explore.",
          informs: ["Q04"],
          status: "not-started",
        },
        {
          id: "capability-shortlist",
          title: "Capability shortlist",
          description: "Rank the candidate capabilities by value and effort.",
          informs: ["Q04"],
          status: "not-started",
        },
      ],
    },
    {
      id: "PROTOTYPE",
      number: 4,
      name: "Prototype",
      tagline: "Make ideas tangible enough to discuss.",
      description: "Sketch the key screens and flows so users can react to something concrete.",
      questionIds: ["Q04"],
      artifacts: [
        {
          id: "wireframes",
          title: "Low-fidelity wireframes",
          description: "Rough screens for the most important user tasks.",
          informs: ["Q04"],
          status: "not-started",
        },
      ],
    },
    {
      id: "TEST",
      number: 5,
      name: "Test",
      tagline: "Validate assumptions and capture learning.",
      description: "Put the prototype in front of users and record what works and what does not.",
      questionIds: ["Q03", "Q04"],
      artifacts: [
        {
          id: "usability-findings",
          title: "Usability test findings",
          description: "What users tried, where they struggled, and what they said.",
          informs: ["Q03", "Q04"],
          status: "not-started",
        },
      ],
    },
  ],

  relevantSources: [
    {
      id: "src-personas",
      title: "NorthStar_User_Personas_v1.pdf",
      pillars: ["USER"],
      phaseName: "Empathize",
      status: "Uploaded",
      createdBy: "Alex Kim",
    },
    {
      id: "src-current-process",
      title: "Current process.pdf",
      pillars: ["USER", "TECH"],
      status: "Awaiting review",
      createdBy: "Alex Kim",
    },
    {
      id: "src-brief",
      title: "Project brief (auto-synthesized).md",
      pillars: ["USER", "DATA", "TECH"],
      status: "Auto-synthesized",
      createdBy: "Discovery Hub",
    },
  ],
};

/** Every artifact the design-thinking method lists for each phase. */
const ARTIFACT_CATALOG: Record<PhaseId, { title: string; description: string }[]> = {
  EMPATHIZE: [
    { title: "Asset map", description: "List the assets, systems and documents the people in scope rely on." },
    { title: "Ecosystem map", description: "Show the people, teams and systems around the work and how they connect." },
    { title: "Empathy map", description: "Capture what each user group thinks, feels, says and does." },
    { title: "Experience map", description: "Trace how users experience the work across channels and touchpoints." },
    { title: "HTA diagram", description: "Break the main task into sub-tasks and steps (hierarchical task analysis)." },
    { title: "Journey map", description: "Follow one user through the process, step by step, with their feelings at each stage." },
    { title: "Landscape map", description: "Summarise the wider context: market, regulation, competitors and trends." },
    { title: "Persona", description: "Represent a main user group with their goals, daily routine and frustrations." },
    { title: "Relationship map", description: "Show who influences whom, and who depends on whom." },
    { title: "Service blueprint", description: "Map front-stage actions, back-stage actions and the systems behind them." },
    { title: "Skill map", description: "Record the skills and knowledge each role has today." },
    { title: "Storyboard", description: "Show a sequence of scenes that illustrate a user's situation." },
    { title: "Usability report", description: "Record how easily users complete the current tasks." },
    { title: "User flow", description: "Show the steps a user takes through the process and the decisions they make." },
  ],
  DEFINE: [
    { title: "Affinity diagram", description: "Group related observations and findings to reveal themes." },
    { title: "Concept map", description: "Link key ideas and terms to show how they relate." },
    { title: "CSD matrix", description: "Sort items into Continue, Start and Discontinue." },
    { title: "Design system", description: "Document the reusable components, patterns and rules for the solution." },
    { title: "Kano model", description: "Classify requirements as basic, performance or delight features." },
    { title: "Mind map", description: "Branch out the problem space from a central idea." },
    { title: "MoSCoW analysis", description: "Rank requirements as Must, Should, Could or Won't have." },
    { title: "RACI matrix", description: "Show who is Responsible, Accountable, Consulted and Informed for each activity." },
    { title: "Scenario map", description: "Describe the situations in which users need the solution." },
    { title: "User-story map", description: "Arrange user stories along the journey and into release slices." },
    { title: "UX roadmap", description: "Plan the user-experience work over time." },
  ],
  IDEATE: [
    { title: "Feasibility, desirability and viability scorecard", description: "Score each idea on whether it can be built, is wanted, and pays back." },
    { title: "Impact–effort matrix", description: "Place ideas by expected impact and the effort needed." },
    { title: "Mood board", description: "Collect images and references that set the look and feel." },
    { title: "RICE method", description: "Score ideas by Reach, Impact, Confidence and Effort." },
  ],
  PROTOTYPE: [
    { title: "Mockup", description: "A high-fidelity static picture of a screen or page." },
    { title: "Prototype", description: "A clickable version that lets users try the main flow." },
    { title: "Site map", description: "Show the pages or screens and how they are organised." },
    { title: "Style guide", description: "Define colours, fonts, spacing and components to use consistently." },
    { title: "Wireflow", description: "Combine wireframes and user flow to show the screens in order." },
    { title: "Wireframe", description: "A simple layout of screens that shows structure, not style." },
  ],
  TEST: [
    { title: "Usability report", description: "Summarise what users did, where they struggled and what to fix." },
    { title: "Storyboard", description: "Show how a tested scenario plays out for the user." },
  ],
};

/** The catalog artifacts first, then any artifact already on the phase that the catalog does not list. */
function withCatalog(phase: DesignPhase): PhaseArtifact[] {
  const existing = new Map(phase.artifacts.map((artifact) => [artifact.title.toLowerCase(), artifact]));
  const listed = ARTIFACT_CATALOG[phase.id].map(({ title, description }) => {
    const found = existing.get(title.toLowerCase());
    if (found) {
      existing.delete(title.toLowerCase());
      return { ...found, description };
    }
    return {
      id: `${phase.id.toLowerCase()}-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
      title,
      description,
      informs: [],
      status: "not-started" as const,
    };
  });
  return [...listed, ...existing.values()];
}

export const placeholderUserDiscovery: PillarDiscovery = {
  ...placeholderUserDiscoveryBase,
  phases: placeholderUserDiscoveryBase.phases.map((phase) => ({ ...phase, artifacts: withCatalog(phase) })),
};