import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { listSourcesForCurrentUser } from "@/features/context/services/serverContextService";
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
 * Loads the same context sources as the overview, so the library is identical.
 * cacheComponents is on, so URL values are read inside Suspense.
 */
export default function PillarDiscoveryPage({ params }: PillarDiscoveryPageProps) {
  return (
    <Suspense fallback={null}>
      {params.then(async ({ projectId, pillar }) => {
        const pillarId = pillarIdFromSlug(pillar);
        if (!pillarId) notFound();
        const sources = await listSourcesForCurrentUser(Number(projectId));
        return <PillarDiscoveryView projectId={projectId} pillarId={pillarId} sources={sources} />;
      })}
    </Suspense>
  );
}
