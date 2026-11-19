import { DownloadIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import type { ArtifactTemplate } from "../types/projectOverview";

export function ArtifactItem({ artifact }: { artifact: ArtifactTemplate }) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-control border border-border-subtle bg-page p-4">
      <div className="flex min-w-0 flex-col gap-1">
        <span className="text-body-medium font-semibold text-fg">{artifact.name}</span>
        <span className="text-caption text-fg-muted">{artifact.description}</span>
      </div>
      <Button variant="secondary" size="sm" aria-label={`Download ${artifact.name}`}>
        <DownloadIcon className="size-4" />
        Download
      </Button>
    </li>
  );
}