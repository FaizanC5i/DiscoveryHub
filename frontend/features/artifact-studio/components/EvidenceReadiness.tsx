import Link from "next/link";
import { badgeClass, cardClass } from "@/features/discovery/utils/class-names";
import type { ArtifactReadiness } from "../types/artifact-studio.types";

interface EvidenceReadinessProps {
  projectId: string;
  artifactName: string;
  readiness: ArtifactReadiness;
}

/** Step 2: how much reviewed evidence the selected artifact has. */
export function EvidenceReadiness({ projectId, artifactName, readiness }: EvidenceReadinessProps) {
  const isFinalReady = readiness.verified === readiness.total;

  return (
    <section aria-labelledby="readiness-title" className={`${cardClass} flex flex-col gap-(--space-4) p-(--space-5)`}>
      <h2
        id="readiness-title"
        className="m-0 text-(length:--font-size-title-small) leading-(--line-height-title-small) font-semibold"
      >
        2. Review evidence readiness · {artifactName}
      </h2>

      <div className="flex flex-wrap items-center gap-(--space-3)">
        <span className="text-(length:--font-size-heading-2) leading-(--line-height-heading-2) font-bold text-(--color-text-brand-primary)">
          {readiness.percent}%
        </span>
        <span className={`${badgeClass.brand} uppercase`}>
          {isFinalReady ? "Final-ready" : "In progress · Not final-ready"}
        </span>
      </div>

      <p className="m-0 font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-subtle)">
        Proposed final-ready rule: all {readiness.total} required items verified, with no unresolved item. Currently{" "}
        {readiness.verified} verified, {readiness.awaitingReview} awaiting review, {readiness.withoutEvidence} without
        evidence.
      </p>

      <table className="w-full border-collapse text-(length:--font-size-body-medium) leading-(--line-height-body-medium)">
        <thead>
          <tr className="text-(length:--font-size-caption) leading-(--line-height-caption) uppercase text-(--color-text-default-subtle)">
            <th scope="col" className="py-(--space-2) text-left font-semibold">Pillar / Status</th>
            <th scope="col" className="py-(--space-2) text-right font-semibold">Verified</th>
            <th scope="col" className="py-(--space-2) text-right font-semibold">Missing</th>
            <th scope="col" className="py-(--space-2) text-right font-semibold">Review</th>
          </tr>
        </thead>
        <tbody>
          {readiness.pillars.map((p) => (
            <tr key={p.pillarId} className="border-t border-(--color-border-default-disabled)">
              <th scope="row" className="py-(--space-3) text-left font-normal">
                {p.label} · {p.status}
              </th>
              <td className="py-(--space-3) text-right">{p.verified}/{p.total}</td>
              <td className="py-(--space-3) text-right">{p.missing}</td>
              <td className="py-(--space-3) text-right">{p.review}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <Link
        href={`/projects/${projectId}/discovery`}
        className="text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold text-(--color-text-brand-primary) no-underline hover:underline"
      >
        View all {readiness.total - readiness.verified} gaps →
      </Link>

      <p className="m-0 text-(length:--font-size-caption) leading-(--line-height-caption) text-(--color-text-default-subtle)">
        Coverage is reviewed completeness, not AI confidence.
      </p>
    </section>
  );
}