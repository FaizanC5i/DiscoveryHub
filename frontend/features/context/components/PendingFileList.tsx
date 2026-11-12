import { Button } from "@/components/ui/Button";
import type { PendingFile } from "../types/source";
import { formatFileSize } from "../utils/fileValidation";
import { UploadStateBadge } from "./SourceStatusBadge";

interface PendingFileListProps {
  files: PendingFile[];
  onRemove?: (id: string) => void;
  onRetry?: (id: string) => void;
}

/** Files on their way to the server, with their state and the actions that apply to each. */
export function PendingFileList({ files, onRemove, onRetry }: PendingFileListProps) {
  if (files.length === 0) return null;

  return (
    <ul className="flex flex-col divide-y divide-border-subtle rounded-card border border-border-subtle">
      {files.map((item) => (
        <li key={item.id} className="flex items-center justify-between gap-4 p-4">
          <div className="flex min-w-0 flex-col gap-1">
            <span className="truncate text-body-medium font-semibold text-fg">{item.file.name}</span>
            <span className="text-caption text-fg-muted">{formatFileSize(item.file.size)}</span>
            {item.error ? <span className="text-caption text-error">{item.error}</span> : null}
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <UploadStateBadge state={item.state} />
            {onRetry && item.state === "failed" ? (
              <Button size="sm" variant="outline" onClick={() => onRetry(item.id)}>
                Retry
              </Button>
            ) : null}
            {onRemove && item.state === "queued" ? (
              <Button
                size="sm"
                variant="outline"
                aria-label={`Remove ${item.file.name}`}
                onClick={() => onRemove(item.id)}
              >
                Remove
              </Button>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}