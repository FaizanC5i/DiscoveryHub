import Link from "next/link";
import { ArrowRightIcon } from "@/components/icons";
import { Badge } from "@/components/ui/Badge";
import { buttonStyles } from "@/components/ui/Button";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { SectionCard } from "@/components/ui/SectionCard";
import type { DiscoveryReadiness } from "../types/projectOverview";
import { getReadinessStatus } from "../utils/getReadinessStatus";

interface DiscoveryReadinessCardProps {
  readiness: DiscoveryReadiness;
  gapsHref: string;
}

// 9999px pill shape is an exception outside the radius tokens (no pill token exists).
const pillBadgeClasses = "gap-1.5 rounded-full px-3 py-1";

export function DiscoveryReadinessCard({ readiness, gapsHref }: DiscoveryReadinessCardProps) {
  const {
    percentComplete,
    reviewed,
    total,
    aiAssessed,
    criticalGaps,
    verified,
    missing,
    awaitingReview,
    nextGap,
  } = readiness;

  return (
    <SectionCard
      title="Discovery"
      action={
        <p className="text-body-small text-fg-muted">
          Readiness is based on reviewed evidence, not project status.
        </p>
      }
    >
      <div className="flex flex-col gap-6 md:flex-row md:items-center">
        <div className="flex items-center gap-4">
          <ProgressRing value={percentComplete} label="Discovery readiness">
            <span className="text-title-large font-semibold text-fg-brand">{percentComplete}%</span>
          </ProgressRing>
          <div className="flex max-w-40 flex-col gap-1">
            <p className="text-title-small font-semibold text-fg-brand">
              {getReadinessStatus(percentComplete)}
            </p>
            <p className="text-caption text-fg-muted">
              {reviewed}/{total} required items reviewed · {aiAssessed} AI-assessed
            </p>
          </div>
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <Badge tone="error" className={pillBadgeClasses}>
              <span aria-hidden="true" className="size-2 rounded-full bg-error" />
              {criticalGaps} critical gaps
            </Badge>
            <Badge tone="success" className={pillBadgeClasses}>
              <span aria-hidden="true" className="size-2 rounded-full bg-success" />
              {verified}/{total} verified
            </Badge>
          </div>

          <p className="text-body-medium text-fg-muted">
            {missing} missing items · {awaitingReview} awaiting review. Final-ready at {total}/{total},
            with no unresolved items.
          </p>

          {nextGap ? (
            <p className="text-body-medium text-fg-secondary">
              <span className="font-semibold text-fg">
                Next gap · {nextGap.topic}:
              </span>{" "}
              {nextGap.question}
            </p>
          ) : null}

          <Link
            href={gapsHref}
            className={buttonStyles({ variant: "outline", size: "sm", className: "self-start" })}
          >
            See {missing} gaps
            <ArrowRightIcon className="size-4" />
          </Link>
        </div>
      </div>
    </SectionCard>
  );
}