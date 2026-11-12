import { ArrowRightIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import { PendingFileList } from "@/features/context/components/PendingFileList";
import type { PendingFile } from "@/features/context/types/source";

interface ProjectDocumentsStepProps {
  projectName: string;
  files: PendingFile[];
  isUploading: boolean;
  onRetry: () => void;
  onOpenProject: () => void;
}

export function ProjectDocumentsStep({
  projectName,
  files,
  isUploading,
  onRetry,
  onOpenProject,
}: ProjectDocumentsStepProps) {
  const hasFailures = files.some((file) => file.state === "failed");

  let status = "All documents are ready.";
  if (isUploading) status = "Processing your documents. Please keep this window open.";
  else if (hasFailures) status = "Some documents could not be processed. Retry them, or open the project and deal with them there.";

  return (
    <div className="flex flex-col gap-6">
      <p className="text-body-large text-fg-muted">
        <span className="font-semibold text-fg">{projectName}</span> is created. {status}
      </p>

      <PendingFileList files={files} onRetry={hasFailures ? onRetry : undefined} />

      <div className="flex flex-col-reverse gap-3 border-t border-border-subtle pt-6 sm:flex-row sm:justify-end">
        {hasFailures ? (
          <>
            <Button variant="outline" disabled={isUploading} onClick={onOpenProject}>
              Open project without these
            </Button>
            <Button loading={isUploading} disabled={isUploading} onClick={onRetry}>
              Retry failed
            </Button>
          </>
        ) : (
          <Button disabled={isUploading} onClick={onOpenProject}>
            Open project
            <ArrowRightIcon className="size-5" />
          </Button>
        )}
      </div>
    </div>
  );
}