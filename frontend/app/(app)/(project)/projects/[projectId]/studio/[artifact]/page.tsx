import type { Metadata } from "next";
import { Suspense } from "react";
import { DraftEditorView } from "@/features/artifact-studio/components/DraftEditorView";

export const metadata: Metadata = {
  title: "Draft editor",
};

interface DraftEditorPageProps {
  params: Promise<{ projectId: string; artifact: string }>;
}

/**
 * Route: /projects/[projectId]/studio/[artifact]   e.g. /projects/101/studio/brd
 * cacheComponents is on, so URL values must be read inside Suspense.
 */
export default function DraftEditorPage({ params }: DraftEditorPageProps) {
  return (
    <Suspense fallback={null}>
      {params.then(({ projectId, artifact }) => (
        <DraftEditorView projectId={projectId} artifactSlug={artifact} />
      ))}
    </Suspense>
  );
}
