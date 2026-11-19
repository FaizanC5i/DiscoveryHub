"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import type { CheckpointCard } from "../types/userDiscovery";

interface UserDiscoveryReviewModalProps {
  card: CheckpointCard;
  busy: boolean;
  error: string | null;
  onApprove: () => void;
  onRegenerate: () => void;
  onClose: () => void;
}

export function UserDiscoveryReviewModal({
  card,
  busy,
  error,
  onApprove,
  onRegenerate,
  onClose,
}: UserDiscoveryReviewModalProps) {
  const proposal = card.pending_proposal;
  const approved = card.current_answer?.status === "APPROVED" ? card.current_answer : null;
  const hasText = !!proposal && proposal.proposed_answer.trim().length > 0;

  return (
    <Modal
      open
      onClose={onClose}
      title={`${card.checkpoint.code} · ${card.checkpoint.name}`}
      dismissible={!busy}
    >
      <div className="flex flex-col gap-6">
        <p className="text-body-medium text-fg-muted">{card.checkpoint.question}</p>

        {error ? <Alert>{error}</Alert> : null}

        {approved ? (
          <section className="flex flex-col gap-2">
            <h3 className="text-body-medium font-semibold text-fg">Approved answer</h3>
            <p className="whitespace-pre-line text-body-medium text-fg">{approved.text}</p>
          </section>
        ) : null}

        {proposal ? (
          <section className="flex flex-col gap-4 rounded-card border border-border-subtle p-4">
            <div className="flex items-center justify-between gap-4">
              <h3 className="text-body-medium font-semibold text-fg">
                {hasText ? "Proposed answer" : "No answer yet"}
              </h3>
              <span className="text-caption text-fg-muted">
                Completion {proposal.completion_score?.toFixed(2) ?? "-"}
              </span>
            </div>

            {hasText ? (
              <p className="whitespace-pre-line text-body-medium text-fg">{proposal.proposed_answer}</p>
            ) : (
              <p className="text-body-small text-fg-muted">
                The agent needs more information for this question before it can write an answer.
              </p>
            )}

            {proposal.missing_information.length > 0 ? (
              <div className="flex flex-col gap-2">
                <h4 className="text-body-small font-semibold text-fg">Missing information</h4>
                <ul className="list-disc pl-5 text-body-small text-fg-secondary">
                  {proposal.missing_information.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {proposal.clarification_questions.length > 0 ? (
              <div className="flex flex-col gap-2">
                <h4 className="text-body-small font-semibold text-fg">Questions for the team</h4>
                <ul className="list-disc pl-5 text-body-small text-fg-secondary">
                  {proposal.clarification_questions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {proposal.evidence.length > 0 ? (
              <div className="flex flex-col gap-2">
                <h4 className="text-body-small font-semibold text-fg">Evidence ({proposal.evidence.length})</h4>
                {proposal.evidence.map((item) => (
                  <details key={item.chunk_id} className="rounded-control bg-page p-3">
                    <summary className="cursor-pointer text-body-small text-fg">
                      {item.source_title}
                      {item.page_number ? ` · page ${item.page_number}` : ""} · chunk {item.chunk_id}
                    </summary>
                    {item.reason ? (
                      <p className="mt-2 text-body-small text-fg-secondary">{item.reason}</p>
                    ) : null}
                    <pre className="mt-2 whitespace-pre-wrap break-words text-caption text-fg-muted">
                      {item.chunk_text}
                    </pre>
                  </details>
                ))}
              </div>
            ) : null}
          </section>
        ) : (
          <p className="text-body-small text-fg-muted">
            There is no proposal for this question. Regenerate to ask the agent again.
          </p>
        )}

        <div className="flex flex-col-reverse gap-3 border-t border-border-subtle pt-6 sm:flex-row sm:justify-between">
          <Button variant="outline" disabled={busy} onClick={onRegenerate}>
            Regenerate
          </Button>
          <Button disabled={!hasText || busy} loading={busy} onClick={onApprove}>
            Approve
          </Button>
        </div>
      </div>
    </Modal>
  );
}