import type { Gap } from "../types/discovery.types";
import { badgeClass } from "../utils/class-names";

/** One missing checkpoint inside a pillar card. */
export function GapCard({ gap }: { gap: Gap }) {
  const isCritical = gap.priority === "critical";

  return (
    <div
      className={`flex flex-col gap-(--space-2) rounded-(--radius-lg) border border-l-(length:--space-1) border-(--color-border-default-disabled) bg-(--color-bg-default-primary) px-(--space-4) py-(--space-3) ${
        isCritical ? "border-l-(--color-status-error)" : "border-l-(--color-status-warning)"
      }`}
    >
      <p
        className={`m-0 uppercase text-(length:--font-size-caption) leading-(--line-height-caption) font-semibold ${
          isCritical ? "text-(--color-red-700)" : "text-(--color-yellow-700)"
        }`}
      >
        {isCritical ? "Critical gap" : "Recommended"}
      </p>
      <p className="m-0 text-(length:--font-size-body-large) leading-(--line-height-body-large) font-semibold">
        {gap.question}
      </p>
      <p className="m-0 font-(family-name:--font-family-secondary) text-(length:--font-size-caption) leading-(--line-height-caption) text-(--color-text-default-subtle)">
        Why it matters: {gap.whyItMatters}
      </p>
      <div className="flex flex-wrap items-center gap-(--space-2) text-(length:--font-size-caption) leading-(--line-height-caption) text-(--color-text-default-subtle)">
        <span>Source:</span>
        <span className={badgeClass.grey}>{gap.source}</span>
        {gap.status === "awaiting-review" && <span className={badgeClass.brand}>Awaiting review</span>}
      </div>
    </div>
  );
}