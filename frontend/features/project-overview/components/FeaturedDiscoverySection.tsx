"use client";

import { useState } from "react";
import { CheckpointReviewPanel } from "@/features/user-discovery/components/CheckpointReviewPanel";
import { FEATURED } from "@/features/user-discovery/constants/featuredCheckpoints";
import { useUserDiscovery } from "@/features/user-discovery/hooks/useUserDiscovery";
import type { CheckpointCard } from "@/features/user-discovery/types/userDiscovery";
import { EndUsersCard } from "./EndUsersCard";
import { ObjectivesCard } from "./ObjectivesCard";
import { ProblemStatementCard } from "./ProblemStatementCard";
import { StakeholdersCard } from "./StakeholdersCard";

interface FeaturedDiscoverySectionProps {
  projectId: number;
}

export function FeaturedDiscoverySection({ projectId }: FeaturedDiscoverySectionProps) {
  const ud = useUserDiscovery(projectId);
  const [openCode, setOpenCode] = useState<string | null>(null);

  function findCard(code: string): CheckpointCard | null {
    return ud.overview?.checkpoints.find((c) => c.checkpoint.code === code) ?? null;
  }

  const panelCard = openCode ? findCard(openCode) : null;

  async function handleApprove(proposalId: number, text: string) {
    await ud.approve(proposalId, text);
    setOpenCode(null);
  }

  return (
    <>
      <ProblemStatementCard
        card={findCard(FEATURED.PROBLEM_STATEMENT)}
        onReview={() => setOpenCode(FEATURED.PROBLEM_STATEMENT)}
      />

      <div className="grid gap-6 md:grid-cols-2">
        <ObjectivesCard
          card={findCard(FEATURED.OBJECTIVES)}
          onReview={() => setOpenCode(FEATURED.OBJECTIVES)}
        />
        <StakeholdersCard
          card={findCard(FEATURED.STAKEHOLDERS)}
          onReview={() => setOpenCode(FEATURED.STAKEHOLDERS)}
        />
      </div>

      <EndUsersCard
        card={findCard(FEATURED.END_USERS)}
        onReview={() => setOpenCode(FEATURED.END_USERS)}
      />

      {panelCard ? (
        <CheckpointReviewPanel
          key={openCode}
          card={panelCard}
          busy={ud.busy}
          error={ud.error}
          onClose={() => setOpenCode(null)}
          onApprove={handleApprove}
        />
      ) : null}
    </>
  );
}
