import type { Metadata } from "next";
import { Suspense } from "react";
import { listSourcesForCurrentUser } from "@/features/context/services/serverContextService";
import { DiscoveryHubView } from "@/features/discovery/components/DiscoveryHubView";

export const metadata: Metadata = {
  title: "Discovery Hub",
};

interface DiscoveryHubPageProps {
  params: Promise<{ projectId: string }>;
}

/**
 * The project layout has already confirmed the visitor owns this project. The page
 * loads the same context sources as the overview. cacheComponents is on, so the id
 * is read inside Suspense.
 */
export default function DiscoveryHubPage({ params }: DiscoveryHubPageProps) {
  return (
    <Suspense fallback={null}>
      {params.then(async ({ projectId }) => {
        const sources = await listSourcesForCurrentUser(Number(projectId));
        return <DiscoveryHubView projectId={projectId} sources={sources} />;
      })}
    </Suspense>
  );
}
