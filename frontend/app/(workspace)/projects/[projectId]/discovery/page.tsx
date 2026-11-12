import type { Metadata } from "next";
import { Suspense } from "react";
import { DiscoveryHubView } from "@/features/discovery/components/DiscoveryHubView";

export const metadata: Metadata = {
  title: "Discovery Hub",
};

interface DiscoveryHubPageProps {
  params: Promise<{ projectId: string }>;
}

/**
 * Route: /projects/[projectId]/discovery
 * cacheComponents is on, so the projectId must be read inside <Suspense>.
 */
export default function DiscoveryHubPage({ params }: DiscoveryHubPageProps) {
  return (
    <Suspense fallback={null}>
      {params.then(({ projectId }) => (
        <DiscoveryHubView projectId={projectId} />
      ))}
    </Suspense>
  );
}