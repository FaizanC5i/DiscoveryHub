import Link from "next/link";
import { cardClass } from "@/features/discovery/utils/class-names";
import type { ArtifactDraft } from "../types/artifact-studio.types";

/** "Incomplete discovery · Not client-ready" card with the evidence snapshot. */
export function DraftStatusBanner({ projectId, draft }: { projectId: string; draft: ArtifactDraft }) {
  const { snapshot } = draft;

  return (
    <section aria-labelledby="draft-status-title" className={`${cardClass} p-(--space-5)`}>
      <h2
        id="draft-status-title"
        className="m-0 mb-(--space-2) text-(length:--font-size-title-small) leading-(--line-height-title-small) font-semibold"
      >
        {draft.isClientReady ? "Discovery complete · Client-ready" : "Incomplete discovery · Not client-ready"}
      </h2>
      <p className="m-0 mb-(--space-2) font-(family-name:--font-family-secondary) text-(length:--font-size-body-small) leading-(--line-height-body-small) text-(--color-text-default-subtle)">
        Snapshot: {snapshot.verified}/{snapshot.total} verified items from {snapshot.sources}{" "}
        {snapshot.sources === 1 ? "source" : "sources"}; {snapshot.missing} missing items flagged;{" "}
        {snapshot.unreviewedExcluded} unreviewed answers excluded.
      </p>
      {!draft.isClientReady && (
        <Link
          href={`/projects/${projectId}/discovery`}
          className="text-(length:--font-size-body-small) leading-(--line-height-body-small) font-semibold text-(--color-text-brand-primary) no-underline hover:underline"
        >
          Resolve in Discovery Hub →
        </Link>
      )}
    </section>
  );
}