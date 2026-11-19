"use client";

import { useEffect, useRef, useState } from "react";
import { CloseIcon } from "@/components/icons";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import type { CheckpointCard } from "../types/userDiscovery";
import { statusOf } from "../utils/cardStatus";

interface CheckpointReviewPanelProps {
  card: CheckpointCard;
  busy: boolean;
  error: string | null;
  onClose: () => void;
  onApprove: (proposalId: number, text: string) => Promise<void>;
  onSubmitInput?: (text: string) => Promise<void>;
}

export function CheckpointReviewPanel({
  card,
  busy,
  error,
  onClose,
  onApprove,
  onSubmitInput,
}: CheckpointReviewPanelProps) {
  const proposal = card.pending_proposal;
  const approved = card.current_answer?.status === "APPROVED" ? card.current_answer : null;
  const [editedText, setEditedText] = useState(proposal?.proposed_answer ?? "");
  const [ownerText, setOwnerText] = useState(card.owner_input ?? "");
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    setEditedText(proposal?.proposed_answer ?? "");
  }, [proposal?.id]);

  useEffect(() => {
    panelRef.current?.focus();
  }, []);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && !busy) onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [busy, onClose]);

  const hasText = editedText.trim().length > 0;
  const textChanged = proposal ? editedText !== proposal.proposed_answer : false;
  const status = statusOf(card) ?? { label: "No answer yet", tone: "neutral" as const };

  async function handleApprove() {
    if (!proposal) return;
    await onApprove(proposal.id, editedText);
  }

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="fixed inset-0 bg-surface-overlay/60"
        aria-hidden="true"
        onClick={() => { if (!busy) onClose(); }}
      />
      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={`Review ${card.checkpoint.name}`}
        tabIndex={-1}
        className="fixed inset-y-0 right-0 z-10 flex h-full w-full max-w-[520px] flex-col border-l border-border-subtle bg-surface shadow-xl outline-none"
      >
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-border-subtle p-6">
          <div className="flex min-w-0 flex-col gap-1.5">
            <span className="text-caption font-medium uppercase tracking-wide text-fg-muted">
              {card.checkpoint.code}
            </span>
            <h2 className="text-title-small font-semibold text-fg">{card.checkpoint.name}</h2>
            <Badge tone={status.tone}>{status.label}</Badge>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            aria-label="Close panel"
            className="inline-flex size-9 shrink-0 items-center justify-center rounded-control text-icon hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-border-brand-strong disabled:opacity-50"
          >
            <CloseIcon className="size-5" />
          </button>
        </div>

        <div className="flex flex-1 flex-col gap-6 overflow-y-auto p-6">
          <p className="text-body-small text-fg-muted">{card.checkpoint.question}</p>

          {error ? <Alert>{error}</Alert> : null}

          {approved ? (
            <section className="flex flex-col gap-2">
              <h3 className="text-body-medium font-semibold text-fg">Approved answer</h3>
              <div className="rounded-card border border-border-subtle bg-page p-4">
                <p className="whitespace-pre-line text-body-medium text-fg">{approved.text}</p>
              </div>
            </section>
          ) : null}

          {proposal ? (
            <section className="flex flex-col gap-4">
              <div className="flex items-center justify-between gap-4">
                <h3 className="text-body-medium font-semibold text-fg">
                  {proposal.proposed_answer.trim() ? "Agent's proposed answer" : "No answer yet"}
                </h3>
                {proposal.completion_score !== null ? (
                  <Badge tone={proposal.completion_score >= 0.7 ? "success" : "warning"}>
                    {`${Math.round(proposal.completion_score * 100)}% complete`}
                  </Badge>
                ) : null}
              </div>

              <Textarea
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                disabled={busy}
                rows={8}
                placeholder="Edit the agent's answer or write your own…"
              />

              {textChanged ? (
                <p className="text-caption text-fg-muted">Your edits will be saved when you approve.</p>
              ) : null}

              {proposal.missing_information.length > 0 ? (
                <details className="rounded-card border border-border-subtle p-4">
                  <summary className="cursor-pointer text-body-small font-semibold text-fg">
                    {`Missing information (${proposal.missing_information.length})`}
                  </summary>
                  <ul className="mt-3 list-disc pl-5 text-body-small text-fg-secondary">
                    {proposal.missing_information.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </details>
              ) : null}

              {proposal.clarification_questions.length > 0 ? (
                <details className="rounded-card border border-border-subtle p-4">
                  <summary className="cursor-pointer text-body-small font-semibold text-fg">
                    {`Questions for the team (${proposal.clarification_questions.length})`}
                  </summary>
                  <ul className="mt-3 list-disc pl-5 text-body-small text-fg-secondary">
                    {proposal.clarification_questions.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </details>
              ) : null}
            </section>
          ) : (
            <p className="text-body-small text-fg-muted">
              No proposal yet. Run User Discovery to generate an answer for this checkpoint.
            </p>
          )}

          {onSubmitInput ? (
            <section className="flex flex-col gap-3 border-t border-border-subtle pt-6">
              <h3 className="text-body-medium font-semibold text-fg">Your input</h3>
              <p className="text-caption text-fg-muted">
                Add what you know about this question. Sending it runs User Discovery again for this checkpoint.
              </p>
              <Textarea
                value={ownerText}
                onChange={(e) => setOwnerText(e.target.value)}
                disabled={busy}
                rows={5}
                placeholder="Write your answer or the details the agent should use…"
              />
              <div>
                <Button
                  variant="outline"
                  disabled={ownerText.trim().length === 0 || busy}
                  onClick={() => void onSubmitInput(ownerText)}
                >
                  Send to agent
                </Button>
              </div>
            </section>
          ) : null}
        </div>

        {proposal ? (
          <div className="shrink-0 border-t border-border-subtle p-6">
            <Button
              className="w-full"
              disabled={!hasText || busy}
              loading={busy}
              onClick={handleApprove}
            >
              {textChanged ? "Approve with edits" : "Approve"}
            </Button>
          </div>
        ) : null}
      </aside>
    </div>
  );
}
