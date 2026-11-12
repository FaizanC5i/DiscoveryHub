import type { Metadata } from "next";
import { Suspense } from "react";
import { ArtifactStudioView } from "@/features/artifact-studio/components/ArtifactStudioView";

export const metadata: Metadata = {
  title: "Artifact Studio",
};

interface ArtifactStudioPageProps {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

/**
 * Route: /projects/[projectId]/studio  (optional ?artifact=BRD)
 * cacheComponents is on, so URL values must be read inside <Suspense>.
 */
export default function ArtifactStudioPage({ params, searchParams }: ArtifactStudioPageProps) {
  return (
    <Suspense fallback={null}>
      {Promise.all([params, searchParams]).then(([{ projectId }, query]) => (
        <ArtifactStudioView
          projectId={projectId}
          initialArtifact={typeof query.artifact === "string" ? query.artifact : undefined}
        />
      ))}
    </Suspense>
  );
}