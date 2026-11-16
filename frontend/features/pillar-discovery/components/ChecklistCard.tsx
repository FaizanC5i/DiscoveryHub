"use client";

import { useState } from "react";
import { InfoIcon } from "@/components/icons";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import type { ChecklistQuestion, DesignPhase, PhaseId, PillarProgress } from "../types/pillar-discovery.types";
import { QuestionCard } from "./QuestionCard";

type QuestionFilter = "open" | "all";

interface ChecklistCardProps {
  title: string; // "User Discovery checklist"
  description: string;
  progress: PillarProgress;
  targetPercent: number;
  questions: ChecklistQuestion[];
  phases: DesignPhase[];
  onGetHelp: (phaseId: PhaseId) => void;
}

/** Top card: progress badges, Open questions / All items toggle, and the question cards. */
export function ChecklistCard({
  title,
  description,
  progress,
  targetPercent,
  questions,
  phases,
  onGetHelp,
}: ChecklistCardProps) {
  const [filter, setFilter] = useState<QuestionFilter>("open");

  const visible = filter === "open" ? questions.filter((q) => q.status === "open") : questions;
  const phaseName = (id: PhaseId) => phases.find((p) => p.id === id)?.name ?? "";

  const toggleClass = (active: boolean) =>
    cn(
      "h-9 rounded-control px-4 text-body-medium font-semibold transition-colors",
      "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong",
      active ? "bg-surface text-fg-brand" : "text-fg hover:text-fg-muted",
    );

  return (
    <Card className="flex flex-col gap-6 p-6 lg:p-8">
      <div className="flex flex-col gap-4">
        <h2 className="text-title-large font-semibold text-fg">{title}</h2>

        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="brand" className="gap-2 rounded-full px-3 py-1 text-body-small">
            <span aria-hidden="true" className="size-2 rounded-full bg-accent" />
            {progress.percent}% / {targetPercent}% target
          </Badge>
          <Badge tone="error" className="gap-2 rounded-full px-3 py-1 text-body-small">
            <span aria-hidden="true" className="size-2 rounded-full bg-error" />
            {progress.criticalGaps} critical gaps
          </Badge>
          <Badge tone="success" className="gap-2 rounded-full px-3 py-1 text-body-small">
            <span aria-hidden="true" className="size-2 rounded-full bg-success" />
            {progress.answered} / {progress.total} answered
          </Badge>
          <span
            role="img"
            aria-label="Only reviewed answers count toward the target. Uploading evidence does not close a gap on its own."
            title="Only reviewed answers count toward the target. Uploading evidence does not close a gap on its own."
            className="inline-flex text-accent"
          >
            <InfoIcon className="size-5" />
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <p className="max-w-3xl text-body-large text-fg-muted">{description}</p>

        <div role="group" aria-label="Show questions" className="flex shrink-0 rounded-control bg-surface-muted p-1">
          <button
            type="button"
            aria-pressed={filter === "open"}
            onClick={() => setFilter("open")}
            className={toggleClass(filter === "open")}
          >
            Open questions ({progress.open})
          </button>
          <button
            type="button"
            aria-pressed={filter === "all"}
            onClick={() => setFilter("all")}
            className={toggleClass(filter === "all")}
          >
            All items ({progress.total})
          </button>
        </div>
      </div>

      {visible.length === 0 ? (
        <p className="rounded-card bg-success-subtle p-4 text-body-medium text-badge-success-fg">
          Every question in this checklist is answered.
        </p>
      ) : (
        <ul
          aria-label="Checklist questions"
          tabIndex={0}
          className="-mx-1 flex snap-x gap-4 overflow-x-auto px-1 pb-3 focus-visible:outline-2 focus-visible:outline-border-brand-strong"
        >
          {visible.map((question) => (
            <li key={question.id} className="flex shrink-0">
              <QuestionCard
                question={question}
                phaseName={phaseName(question.phaseId)}
                onGetHelp={() => onGetHelp(question.phaseId)}
              />
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}