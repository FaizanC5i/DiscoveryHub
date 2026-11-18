"use client";

import { useState } from "react";
import { InfoIcon } from "@/components/icons";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { FEATURED } from "../constants/featuredCheckpoints";
import { useUserDiscovery } from "../hooks/useUserDiscovery";
import type { CheckpointCard } from "../types/userDiscovery";
import { CheckpointReviewPanel } from "./CheckpointReviewPanel";

const FEATURED_CODES = new Set<string>(Object.values(FEATURED));

type Filter = "open" | "all";

function isApproved(card: CheckpointCard): boolean {
  return card.current_answer?.status === "APPROVED";
}

function gapOf(card: CheckpointCard): { label: string; tone: "error" | "warning" | "brand" | "success" } {
  if (isApproved(card)) return { label: "Answered", tone: "success" };
  if (card.chunk_count === 0) return { label: "Critical gap", tone: "error" };
  if (card.pending_proposal?.agent_status === "Needs Clarification") {
    return { label: "Clarification needed", tone: "warning" };
  }
  if (card.pending_proposal) return { label: "Ready to review", tone: "brand" };
  return { label: "Recommended", tone: "warning" };
}

function missingTextOf(card: CheckpointCard): string {
  if (card.pending_proposal?.missing_information[0]) return card.pending_proposal.missing_information[0];
  if (card.chunk_count === 0) return "No evidence in your library yet.";
  return "Answer not generated yet.";
}

function sourcesOf(card: CheckpointCard): string[] {
  return Array.from(new Set(card.evidence.map((item) => item.source_title))).slice(0, 3);
}

interface UserDiscoveryChecklistProps {
  projectId: number;
}

/** Same layout as the pillar checklist: summary tags, open/all toggle, horizontal question cards. */
export function UserDiscoveryChecklist({ projectId }: UserDiscoveryChecklistProps) {
  const ud = useUserDiscovery(projectId);
  const [openId, setOpenId] = useState<number | null>(null);
  const [filter, setFilter] = useState<Filter>("open");

  const cards = (ud.overview?.checkpoints ?? []).filter((c) => !FEATURED_CODES.has(c.checkpoint.code));
  const selected = cards.find((c) => c.checkpoint.id === openId) ?? null;
  const answeredCount = cards.filter(isApproved).length;
  const openCount = cards.length - answeredCount;
  const criticalCount = cards.filter((c) => !isApproved(c) && c.chunk_count === 0).length;
  const percent = cards.length ? Math.round((answeredCount / cards.length) * 100) : 0;
  const visible = filter === "open" ? cards.filter((c) => !isApproved(c)) : cards;

  async function handleApprove(proposalId: number, text: string, proposedText: string) {
    const edited = text.trim() !== proposedText.trim();
    const ok = await ud.approve(proposalId, edited ? text : undefined);
    if (ok) setOpenId(null);
  }

  const toggleClass = (active: boolean) =>
    cn(
      "h-9 rounded-control px-4 text-body-medium font-semibold transition-colors",
      "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong",
      active ? "bg-surface text-fg-brand" : "text-fg hover:text-fg-muted",
    );

  return (
    <Card className="flex flex-col gap-6 p-6 lg:p-8">
      <div className="flex flex-col gap-4">
        <h2 className="text-title-large font-semibold text-fg">User Discovery checklist</h2>

        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="brand" className="gap-2 rounded-full px-3 py-1 text-body-small">
            <span aria-hidden="true" className="size-2 rounded-full bg-accent" />
            {percent}% answered
          </Badge>
          <Badge tone="error" className="gap-2 rounded-full px-3 py-1 text-body-small">
            <span aria-hidden="true" className="size-2 rounded-full bg-error" />
            {criticalCount} critical gaps
          </Badge>
          <Badge tone="success" className="gap-2 rounded-full px-3 py-1 text-body-small">
            <span aria-hidden="true" className="size-2 rounded-full bg-success" />
            {answeredCount} / {cards.length} answered
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
        <p className="max-w-3xl text-body-large text-fg-muted">
          Questions for each User Discovery checkpoint. Open a question to review the agent&apos;s answer or add your own.
        </p>

        <div role="group" aria-label="Show questions" className="flex shrink-0 rounded-control bg-surface-muted p-1">
          <button
            type="button"
            aria-pressed={filter === "open"}
            onClick={() => setFilter("open")}
            className={toggleClass(filter === "open")}
          >
            Open questions ({openCount})
          </button>
          <button
            type="button"
            aria-pressed={filter === "all"}
            onClick={() => setFilter("all")}
            className={toggleClass(filter === "all")}
          >
            All items ({cards.length})
          </button>
        </div>
      </div>

      {ud.error ? (
        <p role="alert" className="text-body-small text-error">
          {ud.error}
        </p>
      ) : null}

      {ud.overview?.running ? <Spinner label="Generating answers for the User Discovery questions..." /> : null}

      {!ud.overview ? <p className="text-body-small text-fg-muted">Loading...</p> : null}

      {ud.overview && visible.length === 0 ? (
        <p className="rounded-card bg-success-subtle p-4 text-body-medium text-badge-success-fg">
          Every question in this checklist is answered.
        </p>
      ) : (
        <ul
          aria-label="Checklist questions"
          tabIndex={0}
          className="-mx-1 flex snap-x gap-4 overflow-x-auto px-1 pb-3 focus-visible:outline-2 focus-visible:outline-border-brand-strong"
        >
          {visible.map((card) => {
            const gap = gapOf(card);
            const approved = isApproved(card);
            const sources = sourcesOf(card);
            return (
              <li key={card.checkpoint.id} className="flex shrink-0">
                <article
                  aria-labelledby={`question-${card.checkpoint.id}`}
                  className="flex w-90 shrink-0 snap-start flex-col gap-3 rounded-card border border-border-disabled bg-surface p-5"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-caption font-semibold text-fg-muted">
                      {card.checkpoint.code} · {approved ? "ANSWERED" : "OPEN"}
                    </p>
                    <Badge tone={gap.tone} className="rounded-full px-3">
                      {gap.label}
                    </Badge>
                  </div>

                  <h3 id={`question-${card.checkpoint.id}`} className="text-title-small font-semibold text-fg">
                    {card.checkpoint.question}
                  </h3>

                  <p className="line-clamp-2 text-body-medium text-fg-muted">
                    <span className="font-semibold text-fg">{approved ? "Answer:" : "Missing:"}</span>{" "}
                    {approved ? card.current_answer?.text : missingTextOf(card)}
                  </p>

                  <div className="flex flex-wrap items-center gap-2 text-caption text-fg-muted">
                    <span>Source:</span>
                    {sources.length === 0 ? <span>None yet</span> : null}
                    {sources.map((source) => (
                      <Badge key={source} tone="neutral" className="rounded-full px-2.5">
                        {source}
                      </Badge>
                    ))}
                  </div>

                  <div className="mt-auto flex flex-wrap items-center gap-4 border-t border-border-disabled pt-4">
                    <Button variant="secondary" size="sm" onClick={() => setOpenId(card.checkpoint.id)}>
                      {approved ? "View answer" : "Answer"}
                    </Button>
                  </div>
                </article>
              </li>
            );
          })}
        </ul>
      )}

      {selected ? (
        <CheckpointReviewPanel
          key={selected.checkpoint.id}
          card={selected}
          busy={ud.busy}
          error={ud.error}
          onClose={() => setOpenId(null)}
          onApprove={(proposalId, text) =>
            handleApprove(proposalId, text, selected.pending_proposal?.proposed_answer ?? "")
          }
          onSubmitInput={async (text) => {
            await ud.submitInput(selected.checkpoint.id, text);
          }}
        />
      ) : null}
    </Card>
  );
}
