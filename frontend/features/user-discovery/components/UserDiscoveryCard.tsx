"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { YetToBeDone } from "@/components/ui/YetToBeDone";
import { OverviewSection } from "@/features/project-overview/components/OverviewSection";
import { useUserDiscovery } from "../hooks/useUserDiscovery";
import { statusOf } from "../utils/cardStatus";
import { UserDiscoveryReviewModal } from "./UserDiscoveryReviewModal";

interface UserDiscoveryCardProps {
  projectId: number;
}

export function UserDiscoveryCard({ projectId }: UserDiscoveryCardProps) {
  const ud = useUserDiscovery(projectId);
  const [openId, setOpenId] = useState<number | null>(null);

  const cards = ud.overview?.checkpoints ?? [];
  const approvedCount = cards.filter((c) => c.current_answer?.status === "APPROVED").length;
  const mappingPending = ud.overview?.pending_mapping_chunks ?? 0;
  const running = ud.overview?.running ?? false;
  const canRun = !!ud.overview && !running && !ud.busy;
  const selected = cards.find((c) => c.checkpoint.id === openId) ?? null;

  return (
    <OverviewSection
      title="User Discovery"
      badge={<Badge tone="brand">{`${approvedCount} of ${cards.length} approved`}</Badge>}
      action={
        <Button size="sm" variant="outline" disabled={!canRun} onClick={() => void ud.startRun()}>
          Run User Discovery
        </Button>
      }
    >
      {ud.error ? (
        <p role="alert" className="text-body-small text-error">
          {ud.error}
        </p>
      ) : null}

      {running ? <Spinner label="Generating answers for the User Discovery questions..." /> : null}

      {mappingPending > 0 ? (
        <p className="text-body-small text-fg-muted">
          {`Waiting for ${mappingPending} chunks to finish mapping before User Discovery can run.`}
        </p>
      ) : null}

      {!ud.overview ? <p className="text-body-small text-fg-muted">Loading...</p> : null}

      {ud.overview && cards.length === 0 ? <YetToBeDone /> : null}

      <ul className="flex flex-col divide-y divide-border-subtle">
        {cards.map((card) => {
          const status = statusOf(card);
          return (
            <li key={card.checkpoint.id} className="flex items-center justify-between gap-4 py-3">
              <div className="flex min-w-0 flex-col gap-1">
                <span className="text-body-medium font-semibold text-fg">
                  {`${card.checkpoint.code} · ${card.checkpoint.name}`}
                </span>
                <span className="text-caption text-fg-muted">{`${card.chunk_count} chunks`}</span>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <Badge tone={status.tone}>{status.label}</Badge>
                <Button size="sm" variant="outline" onClick={() => setOpenId(card.checkpoint.id)}>
                  Review
                </Button>
              </div>
            </li>
          );
        })}
      </ul>

      {selected ? (
        <UserDiscoveryReviewModal
          card={selected}
          busy={ud.busy}
          error={ud.error}
          onClose={() => setOpenId(null)}
          onApprove={async () => {
            if (!selected.pending_proposal) return;
            const ok = await ud.approve(selected.pending_proposal.id);
            if (ok) setOpenId(null);
          }}
          onRegenerate={async () => {
            const ok = await ud.regenerate(selected.checkpoint.id);
            if (ok) setOpenId(null);
          }}
        />
      ) : null}
    </OverviewSection>
  );
}