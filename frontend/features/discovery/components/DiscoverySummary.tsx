import Link from "next/link";
import type { DiscoveryStats } from "../types/discovery.types";
import { badgeClass, badgeMedium, buttonClass, cardClass } from "../utils/class-names";
import { ArrowRightIcon, InfoIcon } from "./icons";

interface DiscoverySummaryProps {
  projectId: string;
  stats: DiscoveryStats;
  targetPercent: number;
}

/** Top card: headline, three status badges, explanation, and Generate BRD. */
export function DiscoverySummary({ projectId, stats, targetPercent }: DiscoverySummaryProps) {
  return (
    <section
      aria-labelledby="discovery-summary-title"
      className={`${cardClass} grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_auto] items-end gap-(--space-6) p-(--space-5) lg:p-(--space-7)`}
    >
      <div>
        <h2
          id="discovery-summary-title"
          className="m-0 mb-(--space-4) text-(length:--font-size-heading-6) leading-(--line-height-heading-6) lg:text-(length:--font-size-heading-4) lg:leading-(--line-height-heading-4) font-semibold"
        >
          Discovery is {stats.percent}% complete, with {stats.criticalGaps} areas identified for further review.
        </h2>

        <div className="mb-(--space-4) flex flex-wrap gap-(--space-2)">
          <span className={`${badgeClass.brand} ${badgeMedium}`}>
            <span aria-hidden="true" className="size-(--space-2) rounded-full bg-(--color-primary-default)" />
            {stats.percent}% / {targetPercent}% target
          </span>
          <span className={`${badgeClass.error} ${badgeMedium}`}>
            <span aria-hidden="true" className="size-(--space-2) rounded-full bg-(--color-status-error)" />
            {stats.criticalGaps} critical gaps
          </span>
          <span className={`${badgeClass.success} ${badgeMedium}`}>
            <span aria-hidden="true" className="size-(--space-2) rounded-full bg-(--color-status-success)" />
            {stats.verified} / {stats.total} verified
          </span>
        </div>

        <p className="m-0 max-w-[72ch] font-(family-name:--font-family-secondary) text-(length:--font-size-body-large) leading-(--line-height-body-large) text-(--color-text-default-subtle)">
          {stats.noEvidence} checkpoints have no evidence yet and {stats.awaitingReview} have evidence waiting
          for your review. Reach {targetPercent}% with zero critical gaps for client-ready deliverables.
          <span
            title="Only answers approved by a person count toward readiness. AI scores do not."
            className="ml-(--space-1) inline-flex align-[-0.125em] text-(--color-primary-default)"
          >
            <InfoIcon />
          </span>
        </p>
      </div>

      <div className="flex flex-col items-start lg:items-end gap-(--space-2)">
        <p className="m-0 text-left lg:text-right text-(length:--font-size-caption) leading-(--line-height-caption) text-(--color-text-default-subtle)">
          Opens the Artifact Studio.
          <br />
          {stats.criticalGaps} critical gaps stay open here.
        </p>
        <Link
          href={`/projects/${projectId}/studio?artifact=BRD`}
          className={`${buttonClass.secondary} px-(--space-5) py-(--space-3)`}
        >
          Generate BRD
          <ArrowRightIcon />
        </Link>
      </div>
    </section>
  );
}