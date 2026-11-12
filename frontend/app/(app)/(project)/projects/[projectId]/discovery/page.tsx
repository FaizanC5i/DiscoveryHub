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
 * The project layout has already confirmed the visitor owns this project, so the
 * page only needs the id. cacheComponents is on, so the id is read inside Suspense.
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
