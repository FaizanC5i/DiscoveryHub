import Link from "next/link";
import type { Pillar } from "../types/discovery.types";
import { badgeClass, buttonClass, cardClass } from "../utils/class-names";
import { toPercent } from "../utils/discovery-stats";
import { GapCard } from "./GapCard";
import { ArrowRightIcon } from "./icons";

const RING_SIZE = 40; // = --space-10
const RING_STROKE = 4; // = --space-1

/** Circular progress showing the % of verified checkpoints. */
function ProgressRing({ percent, label }: { percent: number; label: string }) {
  const radius = (RING_SIZE - RING_STROKE) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - percent / 100);

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      className="relative inline-grid shrink-0 place-items-center"
    >
      <svg width={RING_SIZE} height={RING_SIZE} aria-hidden="true" className="-rotate-90">
        <circle
          cx={RING_SIZE / 2}
          cy={RING_SIZE / 2}
          r={radius}
          fill="none"
          strokeWidth={RING_STROKE}
          className="stroke-(--color-bg-default-disabled)"
        />
        <circle
          cx={RING_SIZE / 2}
          cy={RING_SIZE / 2}
          r={radius}
          fill="none"
          strokeWidth={RING_STROKE}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="stroke-(--color-primary-default)"
        />
      </svg>
      <span
        aria-hidden="true"
        className={`absolute text-(length:--font-size-caption) leading-(--line-height-caption) font-semibold ${
          percent === 0 ? "text-(--color-text-default-subtle)" : "text-(--color-primary-default)"
        }`}
      >
        {percent}%
      </span>
    </div>
  );
}

interface PillarCardProps {
  projectId: string;
  pillar: Pillar;
}

/** One of the three columns: User, Data, Tech Discovery. */
export function PillarCard({ projectId, pillar }: PillarCardProps) {
  const percent = toPercent(pillar.verified, pillar.total);
  const criticalCount = pillar.gaps.filter((g) => g.priority === "critical").length;
  const titleId = `pillar-${pillar.id}-title`;

  return (
    <article aria-labelledby={titleId} className={`${cardClass} flex min-w-0 flex-col gap-(--space-4) p-(--space-5)`}>
      <div className="flex items-start justify-between gap-(--space-3)">
        <div>
          <h3 id={titleId} className="m-0 text-(length:--font-size-title-medium) leading-(--line-height-title-medium) font-semibold">
            {pillar.name}
          </h3>
          <p className="m-0 mt-(--space-1) font-(family-name:--font-family-secondary) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) text-(--color-text-default-subtle)">
            {pillar.description}
          </p>
        </div>
        <ProgressRing percent={percent} label={`${pillar.name}: ${percent}% verified`} />
      </div>

      {pillar.gaps.length > 0 ? (
        <>
          <div className="flex items-center justify-between">
            <h4 className="m-0 uppercase text-(length:--font-size-caption) leading-(--line-height-caption) font-semibold text-(--color-text-default-subtle)">
              What&apos;s missing ({pillar.gaps.length})
            </h4>
            {criticalCount > 0 && <span className={badgeClass.error}>{criticalCount} critical</span>}
          </div>
          {/* Scrollable list, 352px tall (--space-64 + --space-24). tabIndex lets keyboard users scroll. */}
          <ul
            tabIndex={0}
            aria-label={`${pillar.name} gaps`}
            className="m-0 flex max-h-[calc(var(--space-64)+var(--space-24))] list-none flex-col gap-(--space-3) overflow-y-auto p-0 pr-(--space-1)"
          >
            {pillar.gaps.map((gap) => (
              <li key={gap.id}>
                <GapCard gap={gap} />
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className="m-0 rounded-(--radius-lg) bg-(--color-status-success-light) p-(--space-4) text-(--color-green-700)">
          Every checkpoint in this pillar is verified.
        </p>
      )}

      <div className="mt-auto">
        {/* PLACEHOLDER route: the per-pillar page is not designed yet. */}
        <Link
          href={`/projects/${projectId}/discovery/${pillar.id.toLowerCase()}`}
          className={`${buttonClass.primary} w-full px-(--space-5) py-(--space-3) uppercase`}
        >
          Open {pillar.name}
          <ArrowRightIcon />
        </Link>
      </div>
    </article>
  );
}