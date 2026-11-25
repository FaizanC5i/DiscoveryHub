"use client";

import { useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { useUserDiscovery } from "../hooks/useUserDiscovery";
import { CheckpointReviewPanel } from "./CheckpointReviewPanel";

interface ProposedAnswersDialogProps {
  projectId: number;
  open: boolean;
  onClose: () => void;
}

/** Every pending proposal that has an answer. Opening one shows the same review panel as the User Discovery page. */
export function ProposedAnswersDialog({ projectId, open, onClose }: ProposedAnswersDialogProps) {
  return (
    <Modal open={open} onClose={onClose} title="Proposed answers">
      <ProposedAnswersList projectId={projectId} />
    </Modal>
  );
}

function ProposedAnswersList({ projectId }: { projectId: number }) {
  const ud = useUserDiscovery(projectId);
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);

  const cards = ud.overview?.checkpoints ?? [];
  const items = cards.flatMap((card) => {
    const proposal = card.pending_proposal;
    if (!proposal || !proposal.proposed_answer.trim()) return [];
    return [
      {
        card,
        proposalId: proposal.id,
        text: proposal.proposed_answer,
        needsClarification: proposal.agent_status === "Needs Clarification",
      },
    ];
  });
  const selected = cards.find((card) => card.checkpoint.id === openId) ?? null;

  const busy = progress !== null || ud.busy;

  async function approveAll() {
    setSummary(null);
    let failed = 0;
    for (let index = 0; index < items.length; index += 1) {
      setProgress({ done: index, total: items.length });
      const ok = await ud.approve(items[index].proposalId);
      if (!ok) failed += 1;
    }
    setProgress(null);
    setSummary(
      failed === 0
        ? `Approved ${items.length} answers.`
        : `Approved ${items.length - failed} of ${items.length}. ${failed} could not be approved; they may have been replaced by a newer proposal.`,
    );
  }

  if (!ud.overview) return <Spinner label="Loading proposed answers…" />;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-body-medium text-fg-muted">
          {items.length === 0
            ? "No proposed answers are waiting for review."
            : `${items.length} proposed ${items.length === 1 ? "answer" : "answers"} waiting for review.`}
        </p>
        <Button disabled={items.length === 0 || busy} loading={progress !== null} onClick={() => void approveAll()}>
          {progress ? `Approving ${progress.done + 1} of ${progress.total}…` : `Approve all (${items.length})`}
        </Button>
      </div>

      {ud.error && !selected ? <Alert>{ud.error}</Alert> : null}
      {summary ? (
        <p role="status" className="text-body-small text-fg">
          {summary}
        </p>
      ) : null}

      <ul className="flex flex-col gap-4">
        {items.map((item) => (
          <li key={item.proposalId} className="flex flex-col gap-3 rounded-card border border-border-subtle bg-page p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-caption font-semibold uppercase tracking-wide text-fg-muted">
                {item.card.checkpoint.code} · {item.card.checkpoint.name}
              </span>
              {item.needsClarification ? (
                <Badge tone="warning" className="rounded-full px-3">
                  Clarification needed
                </Badge>
              ) : null}
            </div>
            <button
              type="button"
              onClick={() => setOpenId(item.card.checkpoint.id)}
              className="text-left text-body-small font-semibold text-fg hover:text-fg-brand focus-visible:outline-2 focus-visible:outline-border-brand-strong"
            >
              {item.card.checkpoint.question}
            </button>
            <p className="max-h-48 overflow-y-auto whitespace-pre-line text-body-small text-fg">{item.text}</p>
            <div className="flex flex-wrap justify-end gap-2">
              <Button size="sm" variant="outline" disabled={busy} onClick={() => setOpenId(item.card.checkpoint.id)}>
                Answer
              </Button>
              <Button size="sm" variant="secondary" disabled={busy} onClick={() => void ud.approve(item.proposalId)}>
                Approve
              </Button>
            </div>
          </li>
        ))}
      </ul>

      {selected ? (
        <CheckpointReviewPanel
          key={selected.checkpoint.id}
          card={selected}
          busy={ud.busy}
          error={ud.error}
          onClose={() => setOpenId(null)}
          onApprove={async (proposalId, text) => {
            const proposedText = selected.pending_proposal?.proposed_answer ?? "";
            const edited = text.trim() !== proposedText.trim();
            const ok = await ud.approve(proposalId, edited ? text : undefined);
            if (ok) setOpenId(null);
          }}
          onSubmitInput={async (text) => {
            await ud.submitInput(selected.checkpoint.id, text);
          }}
        />
      ) : null}
    </div>
  );
}
