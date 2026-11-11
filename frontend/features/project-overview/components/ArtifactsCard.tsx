import Link from "next/link";
import { ArrowRightIcon } from "@/components/icons";
import { Badge } from "@/components/ui/Badge";
import { buttonStyles } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/SectionCard";
import type { ArtifactTemplate } from "../types/projectOverview";
import { ArtifactItem } from "./ArtifactItem";

interface ArtifactsCardProps {
  draftCount: number;
  artifacts: ArtifactTemplate[];
  studioHref: string;
}

export function ArtifactsCard({ draftCount, artifacts, studioHref }: ArtifactsCardProps) {
  return (
    <SectionCard
      title="Artifacts"
      action={
        draftCount > 0 ? (
          <Badge>
            {draftCount} {draftCount === 1 ? "draft" : "drafts"}
          </Badge>
        ) : null
      }
    >
      <p className="text-body-medium text-fg-muted">
        Artifact Studio reads from the same library. You can generate drafts now; doing so does not
        raise discovery readiness.
      </p>

      <Link href={studioHref} className={buttonStyles({ size: "sm", className: "self-start" })}>
        Create Artifacts
        <ArrowRightIcon className="size-4" />
      </Link>

      <section aria-labelledby="available-artifacts-heading" className="flex flex-col gap-3">
        <h3 id="available-artifacts-heading" className="text-body-medium font-semibold text-fg">
          Available artifacts
        </h3>
        <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {artifacts.map((artifact) => (
            <ArtifactItem key={artifact.id} artifact={artifact} />
          ))}
        </ul>
      </section>
    </SectionCard>
  );
}