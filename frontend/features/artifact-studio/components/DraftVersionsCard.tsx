import { buttonClass, cardClass } from "@/features/discovery/utils/class-names";
import type { DraftVersion } from "../types/artifact-studio.types";

interface DraftVersionsCardProps {
  versions: DraftVersion[];
  isSaving: boolean;
  onSaveVersion: () => void;
}

/** Small card: current version, history link, Save new version. */
export function DraftVersionsCard({ versions, isSaving, onSaveVersion }: DraftVersionsCardProps) {
  const current = versions.find((v) => v.isCurrent) ?? versions[versions.length - 1];

  return (
    <section aria-labelledby="versions-title" className={`${cardClass} flex flex-col gap-(--space-3) p-(--space-5)`}>
      <h2
        id="versions-title"
        className="m-0 text-(length:--font-size-caption) leading-(--line-height-caption) font-semibold uppercase text-(--color-text-default-subtle)"
      >
        Versions
      </h2>
      <p className="m-0 text-(length:--font-size-body-small) leading-(--line-height-body-small)">
        {current ? `v${current.number} · Current · ${current.label}` : "No versions yet"}{" "}
        {/* PLACEHOLDER: version history has no design yet. */}
        <button
          type="button"
          className="cursor-pointer border-0 bg-transparent p-0 font-semibold text-(--color-text-brand-primary) hover:underline"
        >
          View history
        </button>
      </p>
      <div>
        <button type="button" onClick={onSaveVersion} disabled={isSaving} className={`${buttonClass.subtle} disabled:opacity-70`}>
          {isSaving ? "Saving…" : "Save new version"}
        </button>
      </div>
    </section>
  );
}