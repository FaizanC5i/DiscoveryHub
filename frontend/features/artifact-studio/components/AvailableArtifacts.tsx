import Link from "next/link";
import { ArrowRightIcon, DownloadIcon } from "@/features/discovery/components/icons";
import { badgeClass, buttonClass, cardClass } from "@/features/discovery/utils/class-names";
import type { ArtifactType, AvailableArtifact } from "../types/artifact-studio.types";

interface AvailableArtifactsProps {
  projectId: string;
  artifacts: AvailableArtifact[];
  types: ArtifactType[];
}

/** Top card: artifacts already generated, with Download (ready) or Open (draft). */
export function AvailableArtifacts({ projectId, artifacts, types }: AvailableArtifactsProps) {
  return (
    <section aria-labelledby="available-artifacts-title" className={`${cardClass} p-(--space-5)`}>
      <h2
        id="available-artifacts-title"
        className="m-0 mb-(--space-4) text-(length:--font-size-body-large) leading-(--line-height-body-large) font-semibold"
      >
        Available artifacts
      </h2>

      <ul className="m-0 grid list-none grid-cols-1 gap-(--space-3) p-0 md:grid-cols-3">
        {artifacts.map((artifact) => {
          const type = types.find((t) => t.code === artifact.code);
          if (!type) return null;
          const isDraft = artifact.status === "draft";

          return (
            <li
              key={artifact.code}
              className="flex items-center justify-between gap-(--space-3) rounded-(--radius-md) border border-(--color-border-default-disabled) bg-(--color-bg-brand-subtle)/40 p-(--space-3)"
            >
              <div className="min-w-0">
                <p className="m-0 flex items-center gap-(--space-2) text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold">
                  {type.name}
                  {isDraft && <span className={badgeClass.brand}>Draft</span>}
                </p>
                <p className="m-0 text-(length:--font-size-caption) leading-(--line-height-caption) text-(--color-text-default-subtle)">
                  {type.description}
                </p>
              </div>

              {isDraft ? (
                <Link
                  href={`/projects/${projectId}/studio/${artifact.code.toLowerCase()}`}
                  className={`${buttonClass.secondary} px-(--space-3) py-(--space-1)`}
                >
                  Open
                  <ArrowRightIcon />
                </Link>
              ) : (
                // PLACEHOLDER: download needs the export API.
                <button type="button" className={`${buttonClass.secondary} px-(--space-3) py-(--space-1)`}>
                  <DownloadIcon />
                  Download
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}