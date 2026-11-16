import type { ChecklistQuestion, DesignPhase, PillarProgress } from "../types/pillar-discovery.types";

/** Checklist totals. Only answered (human-approved) questions count toward the percentage. */
export function getPillarProgress(questions: ChecklistQuestion[]): PillarProgress {
  const answered = questions.filter((q) => q.status === "answered").length;
  const open = questions.filter((q) => q.status === "open");
  const total = questions.length;

  return {
    answered,
    total,
    percent: total === 0 ? 0 : Math.round((answered / total) * 100),
    open: open.length,
    criticalGaps: open.filter((q) => q.priority === "critical").length,
  };
}

/** How many of a phase's questions are still open. */
export function countOpenQuestions(phase: DesignPhase, questions: ChecklistQuestion[]): number {
  return phase.questionIds.filter((id) => questions.find((q) => q.id === id)?.status === "open").length;
}

/** "Helps answer 1 open question" / "Helps answer 2 open questions". */
export function helpsAnswerLabel(openCount: number): string {
  return `Helps answer ${openCount} open ${openCount === 1 ? "question" : "questions"}`;
}

/** 1 -> "01" */
export const phaseNumber = (n: number) => String(n).padStart(2, "0");