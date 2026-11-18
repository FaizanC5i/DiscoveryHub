import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { PillarDiscoveryView } from "@/features/pillar-discovery/components/PillarDiscoveryView";
import { pillarIdFromSlug } from "@/features/pillar-discovery/utils/pillar-slug";

export const metadata: Metadata = {
  title: "User Discovery",
};

interface PillarDiscoveryPageProps {
  params: Promise<{ projectId: string; pillar: string }>;
}

/**
 * Route: /projects/[projectId]/discovery/[pillar]   e.g. /projects/12/discovery/user
 * The "Open User Discovery" button on the Discovery Hub links here.
 * cacheComponents is on, so URL values are read inside Suspense.
 */
export default function PillarDiscoveryPage({ params }: PillarDiscoveryPageProps) {
  return (
    <Suspense fallback={null}>
      {params.then(({ projectId, pillar }) => {
        const pillarId = pillarIdFromSlug(pillar);
        if (!pillarId) notFound();
        return <PillarDiscoveryView projectId={projectId} pillarId={pillarId} />;
      })}
    </Suspense>
  );
}